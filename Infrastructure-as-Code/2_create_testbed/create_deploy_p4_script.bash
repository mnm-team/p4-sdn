#!/bin/bash

# $1 is the name of the topology in json format, have a look at topo_test.json for the sample format.

usage() {
	echo "Execute this script by: bash $0 <topo in json format>"
}
TOPO_JS=$1
[[ -z $TOPO_JS ]] && usage && exit 1  # topology in json format
[[ ! -f $TOPO_JS ]] && echo "File $TOPO_JS not found! Exit..." && exit 2  
#[[ ! -z $1 ]] && TOPO_JS=$1 || TOPO_JS=topo_test.json 

num_vm=$(jq '. | length' $TOPO_JS)

> deploy_p4_sw.bash

for i in $(seq 0 $(($num_vm-1))); do 

	name=$(jq ".[$i].name" $TOPO_JS | cut -f2 -d'"') #remove the heading and trailing \" of the string
	bridges=$(jq ".[$i].bridge" $TOPO_JS)
	num_bridges=$(jq ".[$i].bridge|length" $TOPO_JS)
	vm_type=$(jq ".[$i].type" $TOPO_JS | cut -f2 -d'"')
	ip=$(jq ".[$i].ip" $TOPO_JS | cut -f2 -d'"')
	#echo "Examine $vm_type $name $bridges $ip $num_bridges"
	#echo "Examine $vm_type $name"

	if [[ $vm_type == "switch" ]]; then
		len=$(jq ".[$i].bridge | length" $TOPO_JS)
		len=$(( $len - 1 ))
		s="" # string
	       	for j in $(seq 1 $len); do
			s=${s}"-i $j@eth$j "
	       	done
		#echo $s
		id=$(echo $name | cut -c2-)
		echo "ssh -n res@$name \"sh -c 'mkdir -p pcaps; sudo simple_switch_grpc $s --pcap pcaps --nanolog ipc:///log.ipc --device-id $id --no-p4 --thrift-port 9090 -- --grpc-server-addr 0.0.0.0:50051 --cpu-port 255 &' > /dev/null 2>&1\"" >> deploy_p4_sw.bash
	fi

done

echo "complete creating create_deploy_p4_script.bash for the testbed specified in $TOPO_JS"
