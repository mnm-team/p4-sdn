#!/bin/bash
#run this script as root or sudo
# make sure the template image is available, otherwise, you need to create it beforehand or copy it from somewhere. In the case of the current project, I created it manually using the debian 11 net-install CD

# $1 is the name of the topology in json format, have a look at topo_test.json for the sample format.
usage() {
	echo "Execute this script by: bash $0 <topo in json format>"
}
TOPO_JS=$1
[[ -z $TOPO_JS ]] && usage && exit 1  # topology in json format
[[ ! -f $TOPO_JS ]] && echo "File $TOPO_JS not found! Exit..." && exit 2  

BASE_HOST=/home/res/template/base-fresh.qcow2
BASE_SW=/home/res/template/base-fresh.qcow2
#BASE_IMG=/home/res/template/base-fresh.qcow2
#BASE_HOST=/home/res/template/base-host.qcow2
#BASE_SW=/home/res/template/base-switch.qcow2
#QCOW2_SRC="http://10.209.194.124:8080/static/template"
#QCOW2_SRC="https://syncandshare.lrz.de/getlink/fig44bCmzi6p9PeaazCRC/base-fresh.qcow2"
QCOW2_SRC="https://syncandshare.lrz.de/dl/fig44bCmzi6p9PeaazCRC/base-fresh.qcow2"
PUBKEY=/home/res/.ssh/id_rsa.pub


[[ ! -f $BASE_HOST ]] && ( mkdir -p $(dirname $BASE_HOST); cd $(dirname $BASE_HOST); wget $QCOW2_SRC )
#[[ ! -f $BASE_SW ]] && ( mkdir -p $(dirname $BASE_SW); cd $(dirname $BASE_SW); wget $QCOW2_SRC/$(basename $BASE_SW) )

[[ ! -f $BASE_HOST || ! -f $BASE_SW ]] && echo "file $BASE_HOST or $BASE_SW does not exist, exit" && exit 1

num_vm=$(jq '. | length' $TOPO_JS)
echo "number of VMs = $num_vm"

MNT="/mnt" #MOUNT POINT
MNT_HOME="$MNT/home/res" # MOUNT HOME
NETWORK_XML="sample_network_xml"
NUM_LINE_NETWORK_XML=$(wc -l < $NETWORK_XML)
#echo $NUM_LINE_NETWORK_XML
QEMU_XML_SRC="/etc/libvirt/qemu"
QEMU_IMG_SRC="/var/lib/libvirt/images"


# create the bridge manager, which will be used as the management network o connect to the inside VMs.
ovs-vsctl add-br br_man
ip a a 172.16.0.254/24 brd 172.16.0.255 dev br_man
ip l s br_man up
# enable the default network, which is connected to by KVM VM by default
apt install dnsmasq-base
sed -i 's/122/123/g' /etc/libvirt/qemu/networks/default.xml #to avoid possible conflicts with the IP range used by the outer KVM-based VM. The next command may fail when such a conflict occurs.
virsh net-start default
# Generate rsa keypair for accessing from outer VM to inner VMs without password
mkdir -p /home/res/.ssh
if [[ ! -f /home/res/.ssh/id_rsa ]]; then
	ssh-keygen -b 2048 -t rsa -f /home/res/.ssh/id_rsa -q -N ""
fi
mkdir -p /root/.ssh
cp /home/res/.ssh/id_rsa /root/.ssh/


for i in $(seq 0 $(($num_vm-1))); do 

	name=$(jq ".[$i].name" $TOPO_JS | cut -f2 -d'"') #remove the heading and trailing \" of the string
	bridges=$(jq ".[$i].bridge" $TOPO_JS)
	num_bridges=$(jq ".[$i].bridge|length" $TOPO_JS)
	vm_type=$(jq ".[$i].type" $TOPO_JS | cut -f2 -d'"')
	ip=$(jq ".[$i].ip" $TOPO_JS | cut -f2 -d'"')
	echo "Create $vm_type $name $bridges $ip $num_bridges"

	# uncomment the next line to ignore the critical actions below
	#continue

	#### clone
	#virsh suspend server1
	#virt-clone --original server1 --name $name --auto-clone
	#virsh resume server1

	if [[ $vm_type == "host" || $vm_type == "server" ]]; then
		cp $BASE_HOST $QEMU_IMG_SRC/$name.qcow2
	else
		cp $BASE_SW $QEMU_IMG_SRC/$name.qcow2
	fi

	if [[ $vm_type == "host" ]]; then #set memory=512 MB for hosts
 		virt-install --virt-type kvm --name $name --disk $QEMU_IMG_SRC/$name.qcow2 --import --os-variant debian10 --vcpus 1 --memory 512 --noautoconsole
	else # and memory=1024 MB for other types of VM
 		virt-install --virt-type kvm --name $name --disk $QEMU_IMG_SRC/$name.qcow2 --import --os-variant debian10 --vcpus 1 --memory 1024 --noautoconsole
	fi
	[[ $? != 0 ]] && echo "Problem with KVM setup, might be critical if support for KVM is not enabled in BIOS" && exit 1

        virsh destroy $name

	### mount
	echo "modify qcow2 image of $name"
	modprobe nbd
	qemu-nbd -c /dev/nbd0 $QEMU_IMG_SRC/$name.qcow2
	fdisk -l /dev/nbd0
	partx -a /dev/nbd0
	mount /dev/nbd0p1 $MNT

        # modify 
	echo $name > $MNT/etc/hostname
	sed "s/HOST_REPLACE/$name/g" sample_etc_hosts > $MNT/etc/hosts

        # setup ssh without password from outer machine to the inner VM
        cat $PUBKEY > $MNT_HOME/.ssh/authorized_keys
        grep -w $name /etc/hosts > /dev/null
        [[ $? != 0 ]] && echo "$ip $name" >> /etc/hosts

	# set ip for eth0 of the inner VM, used for management network
	sed "s/IP_REPLACE/$ip/g" sample_interfaces > $MNT/etc/network/interfaces

	if [[ $vm_type == "switch" ]]; then #switch
		for j in $(seq 1 $(($num_bridges-1))); do
			echo "pre-up ip link set eth$j up" >> $MNT/etc/network/interfaces
		done
	elif [[ $vm_type == "host" || $vm_type == "server" ]]; then #host or server or controller
		sed -i "s/auto lo eth0/auto lo eth0 eth1/g" $MNT/etc/network/interfaces
		ipeth1=$(echo $ip | cut -f1,2 -d.)
	       	byte=$(echo $ip | cut -f3 -d.)
		byte=$(( byte+1 ))
		ipeth1=${ipeth1}.${byte}.$(echo $ip | cut -f4 -d.)

		echo >> $MNT/etc/network/interfaces
		echo "iface eth1 inet static" >> $MNT/etc/network/interfaces
		echo "address $ipeth1" >> $MNT/etc/network/interfaces
		echo "netmask 255.255.255.0" >> $MNT/etc/network/interfaces
	fi

	# unmount
	umount $MNT
	qemu-nbd -d /dev/nbd0

	# modify VM's XML:
	s=$(grep -m1 -n interface ${QEMU_XML_SRC}/$name.xml | cut -f1 -d:) # start
	l=$(grep -n interface ${QEMU_XML_SRC}/$name.xml | tail -1 | cut -f1 -d:) # last
	echo "start: $s, last: $l"
	sed -i "${s},${l}d" ${QEMU_XML_SRC}/$name.xml
	s=$(($s-1))

	for br in $(jq ".[$i].bridge[]" $TOPO_JS); do
		br=$(echo $br | cut -f2 -d'"')
		echo "add bridge $br to ${QEMU_XML_SRC}/$name.xml" 
		sed "s/br_replace/$br/" $NETWORK_XML > tmp_xml
		sed -i "$s r tmp_xml" ${QEMU_XML_SRC}/$name.xml
		s=$(($s+$NUM_LINE_NETWORK_XML))
	        # create the corresponding bridge in the outer machine
	        ovs-vsctl add-br $br
	        ip link set $br up
	done

	# define VM again:
	virsh define /etc/libvirt/qemu/$name.xml

	# start VM:
	virsh start $name

done

rm -f tmp_xml

echo "complete creating testbed specified in $TOPO_JS"

#We can deploy P4 switches by the following commands
#bash create_deploy_p4_script.bash $TOPO_JS
#sleep 30
#echo "deploy p4 switches"
#bash deploy_p4_sw.bash
#echo "Now, you need to run the controller app to control the p4 switches"
