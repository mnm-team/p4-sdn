#!/bin/bash

# run the below as user res, i.e., under the directory /home/res/

# Print script commands and exit on errors.
#set -xe


grep LIBVIRT_DEFAULT_URI ~/.bashrc > /dev/null
if [[ $? != 0  ]]; then
       	echo export LIBVIRT_DEFAULT_URI=\'qemu:///system\' >> ~/.bashrc
fi

source ~/.bashrc

sudo apt update

sudo apt install -y tmux tree jq rsync openvswitch-switch 

sudo apt install --no-install-recommends -y qemu-system libvirt-clients libvirt-daemon-system virt-manager qemu-utils

sudo adduser res libvirt

# virt-manager and virt-viewer are only for graphical management of VMs, we can ignore them if we don't need them.
sudo apt install -y virt-manager virt-viewer

# Install vagrant if you want to create a VM using vagrant
#sudo apt install -y vagrant 
#vagrant plugin install vagrant-libvirt


sudo iptables -t nat -A POSTROUTING -o ens3 -j MASQUERADE
sudo sysctl -w net.ipv4.ip_forward=1

# create the bridge manager, which will be used as the management network o connect to the inside VMs.
sudo ovs-vsctl add-br br_man
sudo ip a a 172.16.0.254/24 brd 172.16.0.255 dev br_man
sudo ip l s br_man up

# enable the default network, which is connected to by KVM VM by default
sudo apt install -y dnsmasq-base
sudo virsh net-start default

### enable ssh X forwarding ###
#On your server, make sure /etc/ssh/sshd_config contains:
#X11Forwarding yes
#X11DisplayOffset 10

sudo apt install -y xauth

grep "StrictHostKeyChecking accept-new" /etc/ssh/ssh_config > /dev/null
if [[ $? != 0  ]]; then 
	sudo bash -c 'echo "    StrictHostKeyChecking accept-new" >> /etc/ssh/ssh_config'
	sudo systemctl restart ssh
fi

# Generate rsa keypair for accessing from outer VM to inner VMs without password
mkdir -p ~/.ssh
if [[ ! -f /home/res/.ssh/id_rsa ]]; then
	ssh-keygen -b 2048 -t rsa -f /home/res/.ssh/id_rsa -q -N ""
fi

#install software specific to PROTECT:
sudo apt install -y python3-pip


#then log out and log in again with user res, so the environment and the usergroup are updated.

# sudo -E pip install graphviz
