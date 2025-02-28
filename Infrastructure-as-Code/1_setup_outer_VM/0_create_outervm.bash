#!/bin/bash

# Print script commands and exit on errors.
#set -xe

###########################################################################################
# create the outer machine in either way below (by a cloud image or by a netinstall image, 
# or from a Debian's nocloud image, or from a cloud service like OpenStack).
# As of 2024, I prefer using Debian's nocloud images due to their convenience, see the 3. option below
###########################################################################################

#1. by using a cloud image:
# refer to https://blog.programster.org/create-debian-12-kvm-guest-from-cloud-image

##grep LIBVIRT_DEFAULT_URI ~/.bashrc > /dev/null
##if [[ $? != 0  ]]; then
##        echo export LIBVIRT_DEFAULT_URI=\'qemu:///system\' >> ~/.bashrc
##fi
##source ~/.bashrc
##sudo apt update
##
##sudo apt install --no-install-recommends -y qemu-system libvirt-clients libvirt-daemon-system virt-manager qemu-util
##
##sudo apt install -y cloud-utils whois php-cli php-yaml 
##
##wget https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-generic-amd64.qcow2
##
##mv debian-12-generic-amd64.qcow2 debian-12.qcow2
##
##VM_NAME="template-debian-12"
##DESIRED_SIZE=100G
##sudo qemu-img resize debian-12.qcow2 $DESIRED_SIZE
##wget https://files.programster.org/tutorials/cloud-init/create-debian-12-kvm-guest-from-cloud-image/generate.php
##
### correct the sshPublicKeys in that generate.php file, then continue with the next steps
##php generate.php
##sudo cloud-localds cloud-init.iso cloud-init.cfg
##sudo virt-install \
##  --name $VM_NAME \
##  --memory 4096 \
##  --disk debian12.qcow2,device=disk,bus=virtio \
##  --disk cloud-init.iso,device=cdrom \
##  --os-variant debian10 \
##  --virt-type kvm \
##  --graphics none \
##  --network network=default,model=virtio \
##  --import

# refer to https://blog.programster.org/create-debian-12-kvm-guest-from-cloud-image for further customization after creating the VM.


#2.  by installing it with a netinstall image:
# see: https://wiki.debian.org/KVM#Creating_a_new_guest

##wget https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/debian-11.6.0-amd64-netinst.iso
##export LIBVIRT_DEFAULT_URI='qemu:///system'
##sudo virsh net-list --all
##sudo apt install dnsmasq-base
##sudo virsh net-start default (start the default network, which is connected by KVM guests by default)
##virt-install --virt-type kvm --name bullseye-amd64 --cdrom debian-11.6.0-amd64-netinst.iso --os-variant debian10 --disk size=9 --memory 1000
##(then install debian in guest VM with the GUI of virt-viewer)


#3. From a debian nocloud image, e.g., https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-nocloud-amd64.qcow2

# A nocloud image is convenient, one can boot directly to that image and login as user root without password. On the host machine, we need to install KVM software using the following commands (assume that the host machine is running Ubuntu 22.04 or Debian 11, it should be similar for other Ubuntu or Debian releases): 
# sudo apt update
# sudo apt install --no-install-recommends -y qemu-system libvirt-clients libvirt-daemon-system virt-manager qemu-utils
# sudo apt install -y virt-manager virt-viewer
# sudo apt install -y dnsmasq-base
# sudo virsh net-start default

# Then to boot into the nocloud image, this command can be used:
# sudo virt-install --name=debian12_nocloud --vcpus=2 --memory=2048 --disk debian-12-nocloud-amd64.qcow2 --import --os-variant=debian12
# virt-viewer will show an interactive GUI, where we can login as root user, then install openssh-server, check IP addresses of the machine, create res user... Afterwards, we can ssh from the host machine into this nocloud-based VM to carry out further steps in a convenient way.

#4. From OpenStack, Amazon EC2 ...
