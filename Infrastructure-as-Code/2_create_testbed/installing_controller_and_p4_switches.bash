#!/bin/bash 

#ref: https://github.com/p4lang/tutorials/blob/master/vm-ubuntu-20.04/root-release-bootstrap.sh

## install switch
echo "deb http://download.opensuse.org/repositories/home:/p4lang/Debian_11/ /" | sudo tee /etc/apt/sources.list.d/home:p4lang.list
wget -qO - "http://download.opensuse.org/repositories/home:/p4lang/Debian_11/Release.key" | sudo apt-key add -
sudo apt-get update
sudo apt install --no-install-recommends ca-certificates iproute2 unzip valgrind p4lang-p4c p4lang-bmv2 p4lang-pi

#configure vim for P4 programming:
cd
wget https://raw.githubusercontent.com/p4lang/tutorials/master/vm-ubuntu-20.04/p4.vim
#wget https://raw.githubusercontent.com/p4lang/tutorials/master/vm-ubuntu-20.04/p4_16-mode.el
mkdir .vim
cd .vim
mkdir ftdetect syntax
echo "au BufRead,BufNewFile *.p4      set filetype=p4" >> ftdetect/p4.vim  #not include after #*
echo "set bg=dark" >> ~/.vimrc
mv ~/p4.vim syntax/p4.vim


## install controller

echo "deb http://download.opensuse.org/repositories/home:/p4lang/Debian_11/ /" | sudo tee /etc/apt/sources.list.d/home:p4lang.list
wget -qO - "http://download.opensuse.org/repositories/home:/p4lang/Debian_11/Release.key" | sudo apt-key add -
sudo apt-get update
sudo apt install --no-install-recommends ca-certificates iproute2 unzip valgrind p4lang-p4c p4lang-pi
sudo -E pip3 install -U scapy ipaddr ptf psutil grpcio
sudo -E pip3 install networkx flask flask_restful

# configure vim for P4 programming:
cd
wget https://raw.githubusercontent.com/p4lang/tutorials/master/vm-ubuntu-20.04/p4.vim
#wget https://raw.githubusercontent.com/p4lang/tutorials/master/vm-ubuntu-20.04/p4_16-mode.el
mkdir .vim
cd .vim
mkdir ftdetect syntax
echo "au BufRead,BufNewFile *.p4      set filetype=p4" >> ftdetect/p4.vim  #not include after #*
echo "set bg=dark" >> ~/.vimrc
mv ~/p4.vim syntax/p4.vim

