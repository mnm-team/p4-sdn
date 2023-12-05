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

num_vm=$(jq '. | length' $TOPO_JS)
echo "number of VMs = $num_vm"

for i in $(seq 0 $(($num_vm-1))); do 

	name=$(jq ".[$i].name" $TOPO_JS | cut -f2 -d'"') #remove the heading and trailing \" of the string
	vm_type=$(jq ".[$i].type" $TOPO_JS | cut -f2 -d'"')
	ip=$(jq ".[$i].ip" $TOPO_JS | cut -f2 -d'"')
	echo "Stop $vm_type $name $ip"

	# stop VM:
	virsh shutdown $name
done


echo "complete shutting down all VMs in testbed specified in $TOPO_JS"
