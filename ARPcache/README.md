# Implementing ARPcache

The network topology used in this example contains a loop:

![network topology](topo.svg)

We should to be familiar with the [simple\_demo](../simple_demo) and [simple\_switch](../simple_switch) examples before diving in this ARPcache.

The normal learning switch in [simple\_switch](../simple_switch) broadcasts a packet on all ports (except for the incoming port) if it has not learnt the MAC address of that packet. In a network topology containing loops like the one shown in the picture above, such behaviour would amplify new packets in many rounds and could make the network overloaded and unresponsive. 

In SDN, we can exploit the knowledge of the controller about the network topology to overcome the amplifying of packets in a network containing loops (normally, the controller has a built-in function of detecting the connections between switches (and even connections to hosts), namely topology discovery (see an explanation by Volkan here https://volkan.yazi.ci/blog/post/2013/08/06/sdn-discovery/); in our examples, we haven't implemented that function but simulated it via the encoding of the topology in a json file (topo\_loop.json)). 

The operating mechanism of ARPcache is simple. We set the default behaviour of P4-switches to be: sending unknown packets (those that the switches don't know how to handle due to the absence of rules in their tables) to the controller via the packet-in mechanism (packets sent from SDN devices to the controller) and do not flood them on other ports as in the simple\_switch example. Based on the knowledge of the network topology, the controller can determine the switches in the network and which ports of each switch are connected to end-points (and also which ports are connected to other switches). As the final goal of the broadcasting action in the simple\_switch is to sending the original packet to other end-points, now in this case, the controller can simply use the packet-out mechanism (packets sent by the controller to SDN-devices) to replicate the packet received from a P4-switch to all end-points in the network. Basically, the process is:
+ the end-point sends a packet into the network,
+ the switch, directly connected to that end-point, does not know how to handle that packet, it sends that packet to the controller (via the packet-in mechanism),
+ the controller sends the packets to all other end-points via the packet-out mechanism, using its knowledge of the network topology. At the same time, the controller "caches" the information: that end-point is directly connected to that switch via that port in the format: end-point's IP, end-point's MAC, switch ID, port number.
+ All end-points receive that packet. Only the "pertinent" end-point sends answers to the original sender (and the other end-points should drop that packet). The switch directly connected to the answering end-point asks the controller what to do via the packet-in mechanism, the controller knows the address of the recipient that it cached in the previous step, so it calculates a path between the sender and the receivers based on the topology information and installs forwarding rules in all switches along that path. Now, the communcation between the sender and the receiver can be carried out as usual. In this step, the controller also caches the information of the other end-point in the same format as before: end-point's IP, end-point's MAC, switch ID, port number. Gradually, the controller caches all end-points' information and can install corresponding rules once being asked by an SDN-switches.

## Consider a concret replay

Consider a concrete case in the network topology above.
+ PC1 wants to talk with PC3 (e.g., via the ping command: ping 192.168.1.3), firstly it sends an ARP Request message asking for the MAC address of PC3. This ARP message contains the IP and MAC addresses of PC1.
+ This ARP message reaches switch S1, there's no rule in S1 to handle it. S1 sends this ARP message to the controller via the packet-in mechanism, it also tells that the ingress port of this ARP message is port 1.
+ The controller receives this message from switch S1,
  + the controller parses the content of the message and caches the information: the IP 192.168.1.1 is associated with the MAC address of PC1, say MAC\_PC1, and is reachable via port 1 of switch S1,
  + the controller checks its ARPcache database for information of the destination in the ARP Request message, being 192.168.1.3, and finds no record; hence, it broadcasts the ARP message to all end-points: based on its knowledge of the network topology, it knows that port 1 of each of switches S1, S2 and S3 is connected to end-points, the controller replicates the ARP message and sends them on port 1 of switch S2 and S3 using the packet-out mechanism. As this ARP message originates from port 1 of switch S1, the controller does not send it there.
+ Switches S2 and S3 receive the packet-out messages from the controller and forward them as instructed by the controller. These messages reach PC2 and PC3. PC2 drops it, PC3 answers by an ARP Reply containing PC3's IP and MAC addresses, and PC1's IP and MAC addresses.
+ The ARP Reply of PC3 reaches switch S3, S3 does not know how to handle and asks the controller for instruction via the packet-in mechanism, which also tells the ingress port of this ARP Reply being port 1.
+ The controller receives the ARP Reply from switch S3,
  + it parses the content of the ARP Reply message and caches the information: the IP 192.168.1.3 is associated with the MAC address of PC3, say MAC\_PC3, and is reachable via port 1 of switch S3,
  + the controller checks its ARPcache database for information of the destination in the ARP Reply message, being 192.168.1.1, and finds an existing record, that this IP can be reached via port 1 of switch S1. It calculates the path from the asking switch, being S3, to switch S1, installs corresponding rules in all switches along this path in both directions (from PC1 to PC3, and from PC3 to PC1), and sends the ARP Reply out of port 1 of switch S1 via the packet-out mechanism.
+ Now there are rules in switches S1 and S3 to handle traffic between PC1 and PC3, these PCs can communicate with each other. The controller has also cached the relevant information of PC1 and PC3 in its ARPcache database. A similar process takes place for other traffic as well, e.g., the traffic between PC2 and PC3.

## Implementation




demo with nc:
PC1: nc -lk 12345 -vn
PC2: nc 192.168.1.1 12345 -vn

Explain packet-in and packet-out in code.
