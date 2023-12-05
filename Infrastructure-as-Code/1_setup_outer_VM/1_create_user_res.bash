#!/bin/bash

# after starting the outer VM, we need to run this script as sudo, i.e., sudo bash 1_create_user_res.bash, to create user res (research)

# Print script commands and exit on errors.
set -xe

### create user res
sudo useradd -m -c "Research" res -s /bin/bash -p res
sudo bash -c 'echo "res:res" | chpasswd'
sudo bash -c 'echo "res ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/99_res'
sudo chmod 440 /etc/sudoers.d/99_res

#then logout and login by user res
