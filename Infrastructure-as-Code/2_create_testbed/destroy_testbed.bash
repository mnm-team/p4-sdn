#!/bin/bash
#run this script as root or sudo
# make sure the template image is available, otherwise, you need to create it beforehand or copy it from somewhere. In the case of PROTECT-project, I created it manually using the debian 11 net-install CD

# $1 is the name of the topology in json format, have a look at topo_test.json for the sample format.

usage() {
	echo "Execute this script by: bash $0 <topo in json format>"
}
TOPO_JS=$1
[[ -z $TOPO_JS ]] && usage && exit 1  # topology in json format
[[ ! -f $TOPO_JS ]] && echo "File $TOPO_JS not found! Exit..." && exit 2  

#[[ ! -z $1 ]] && TOPO_JS=$1 || TOPO_JS=topo_test.json # topology in json format

num_vm=$(jq '. | length' $TOPO_JS)
echo "number of VMs = $num_vm"

QEMU_IMG_SRC="/var/lib/libvirt/images"

for i in $(seq 0 $(($num_vm-1))); do 

	name=$(jq ".[$i].name" $TOPO_JS | cut -f2 -d'"') #remove the heading and trailing \" of the string
	bridges=$(jq ".[$i].bridge" $TOPO_JS)
	num_bridges=$(jq ".[$i].bridge|length" $TOPO_JS)
	vm_type=$(jq ".[$i].type" $TOPO_JS | cut -f2 -d'"')
	ip=$(jq ".[$i].ip" $TOPO_JS | cut -f2 -d'"')
	echo "Destroy $vm_type $name $bridges $ip $num_bridges"

	# uncomment the next line to ignore the critical actions below
	#continue

        virsh destroy $name
        virsh undefine $name
	rm -f $QEMU_IMG_SRC/$name.qcow2

	line=$(grep -n -w $name /etc/hosts | tail -1 | cut -f1 -d:)
        [[ ! -z $line ]] && sed -i "${line}d" /etc/hosts

	for br in $(jq ".[$i].bridge[]" $TOPO_JS); do
		br=$(echo $br | cut -f2 -d'"')
	        # remove the corresponding bridge in the outer machine
	        ovs-vsctl del-br $br
	done

done

echo "complete destroying testbed specified in $TOPO_JS"
