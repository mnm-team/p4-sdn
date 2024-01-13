# Create a Testbed for P4-based SDN using KVM and Open vSwitch (instead of using Xen and Linux Bridge):

In another repository (https://github.com/mnm-team/sdn-conflicts/tree/main/topogen), we show how to create SDN infrastructure (OpenFlow-based SDN) using Xen. In this repo, we show an alternative to create a test-bed for P4-based SDN. In general, the script can be adapted to create test-beds for network testing, since the test-bed is built on virtual machines (VM), with appropriate software installed, a VM can be a switch (e.g., using Open vSwitch), a router (e.g., with FRRouting)...

## Goal:

Create a big outer VM, in which a network of KVM-based VMs constituting the test-bed is constructed, these internal KVM-based VMs can be hosts, switches, routers, controllers, security servers or whatever we want to test.

The test-bed is "packed" in a big VM, so that its network is isolated from the outside network, and also isolated from other test-beds in the same physical machine. Therefore, our testing will not influence the other networks and vice versa.

<img src="isolated-testbed.svg" alt="Isolated test-bed" width="70%"/>

## 1. Create outer VM 

The steps are described in the directory 1\_setup\_outer\_VM.
In essence, we assume the existence of the outer VM (or outer machine), then we need to run the script 1\_create\_user\_res.bash and 2\_install\_basic\_software.bash. The outer VM can be created using the provided way described in the script 0\_create\_outervm.bash

The main user of both the outer and inner machines is *res*.

After installing the basic software with the script: 2\_install\_basic\_software.bash, log out and log in again to update the environment variables and the user group (user res belongs to group libvirt)

## 2. Create test-bed (directory 2\_create\_testbed)

File: create\_testbed.bash

The topology for test-bed is specify by the variable TOPO\_JS (topology in json format), which is passed by variable $1 when executing this script.

The test-bed is created using template image base-fresh.qcow2 for all VMs, which can be downloaded at: https://syncandshare.lrz.de/getlink/fig44bCmzi6p9PeaazCRC/base-fresh.qcow2.
However, we can also differentiate between different types of VM, e.g., host, switch, server, controller; in that case, we can customize the base-fresh.qcow2 to make it become template-images for these types of VM. Adapt the variable BASE\_HOST and BASE\_SW in the script for the correct base images.

The template image is created based on the debian11 image: https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/debian-11.6.0-amd64-netinst.iso. We use debian11 for software compatibility in deploying P4 switches and the SDN controller. Alternatively, we can create a template image in a similar way as described in the file 1\_setup\_outer\_VM/0\_create\_outervm.bash. For our project (P4-based SDN project), we need to modify the template image to use the old simple scheme for network interface name (eth0, eth1...) instead of the new "persistent names" scheme (network interfaces are named as ens0, ens1, en0p1...), as it is easier for parsing and for scripting in a program. The network interface naming is described in https://wiki.debian.org/NetworkInterfaceNames.

To recreate a fresh test-bed, we need to first destroy it using the script destroy\_testbed.bash, then run the script create\_testbed.bash as just described above.

Once the test-bed is created, we can access to the outer VM, therefrom we can access to each VM using its name or its IP address specified in the json file (this json file is the input to the script create\_testbed.bash), e.g., `ssh h1` to access to the host h1.


## 3. Installing P4 switches and SDN controller (optionally, specific to the P4-based SDN project)

Follow the instruction in 2\_create\_testbed/installing\_controller\_and\_p4\_switches.bash to install the p4 switches and controller on the corresponding VMs in the test-bed. The instruction is based on https://github.com/p4lang/tutorials/tree/master/vm-ubuntu-20.04

## 4. Explaining the implementation of VM-based test-bed

We illuminate the implementation via the following pictures.

<img src="testbed-explain-1.svg" alt="Explaining testbed 1" width="80%"/>

Each switch or host corresponds to a VM. Their connections are realized via a bridge inbetween. The outer VM has connections to all VM for management purpose (e.g., start/stop a VM, configure its IP addresses...)

<img src="testbed-explain-2.svg" alt="Explaining testbed 2" width="80%"/>

The test-bed can be described in json format. For example, host h1 is connected to bridge br\_s1h1, switch s1 is also connected to this bridge; thus, host h1 and switch s1 are connected. We use Open vSwitch to realize the bridge connecting two VMs. The bridge br\_man (management bridge) is connected to all VMs and also to the outer VM. 

As mentioned before, we use  the old simple scheme for network interface name (eth0, eth1...). Hence, in this example, host h1 has 2 interfaces: eth0 connected to the management bridge br\_man, eth1 connected to the interface eth1 of switch s1 (via bridge br\_s1h1). Likewise, host h2 has 2 interfaces: eth0 connected to br\_man, eth1 to the interface eth2 of switch s1 (via bridge br\_s1h2). Switch s1 has 3 interfaces: eth0 connected to br\_man, eth1 to h1 and eth2 to h2. Note that the first interface eth0 of each VM (h1, h2, s1) is always connected to the management bridge br\_man for the management purpose: to start/stop the VM, configure its IP addresses... The other interfaces (eth1, eth2...) are dedicated for the "production" network corresponding to the test-bed, testing traffic should be sent and received on these interfaces.
