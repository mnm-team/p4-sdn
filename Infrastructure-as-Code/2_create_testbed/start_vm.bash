#!/bin/bash
#run this script as root or sudo
# make sure the template image is available, otherwise, you need to create it beforehand or copy it from somewhere. In the case of PROTECT-project, I created it manually using the debian 11 net-install CD

# $1 is the name of the topology in json format, have a look at topo_test.json for the sample format.
usage() {
	echo "Execute this script by: sudo bash $0 <topo in json format>"
}
TOPO_JS=$1
[[ -z $TOPO_JS ]] && usage && exit 1  # topology in json format
[[ ! -f $TOPO_JS ]] && echo "File $TOPO_JS not found! Exit..." && exit 2  

num_vm=$(jq '. | length' $TOPO_JS)
echo "number of VMs = $num_vm"


# create the bridge manager, which will be used as the management network o connect to the inside VMs.
ovs-vsctl add-br br_man
ip a a 172.16.0.254/24 brd 172.16.0.255 dev br_man
ip l s br_man up

for i in $(seq 0 $(($num_vm-1))); do 

	name=$(jq ".[$i].name" $TOPO_JS | cut -f2 -d'"') #remove the heading and trailing \" of the string
	bridges=$(jq ".[$i].bridge" $TOPO_JS)
	num_bridges=$(jq ".[$i].bridge|length" $TOPO_JS)
	vm_type=$(jq ".[$i].type" $TOPO_JS | cut -f2 -d'"')
	ip=$(jq ".[$i].ip" $TOPO_JS | cut -f2 -d'"')
	echo "Create $vm_type $name $bridges $ip $num_bridges"

	for br in $(jq ".[$i].bridge[]" $TOPO_JS); do
		br=$(echo $br | cut -f2 -d'"')
	        # create the corresponding bridge in the outer machine
	        ovs-vsctl add-br $br
	        ip link set $br up
	done

	# start VM:
	virsh start $name

	# add to /etc/host if not yet available
        grep -w $name /etc/hosts > /dev/null
        [[ $? != 0 ]] && echo "$ip $name" >> /etc/hosts
done


echo "complete starting testbed specified in $TOPO_JS"

bash create_deploy_p4_script.bash $TOPO_JS
sleep 30
echo "deploy p4 switches"
bash deploy_p4_sw.bash
echo "Now, you need to run the controller app to control the p4 switches"
