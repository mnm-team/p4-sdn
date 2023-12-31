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




demo with nc:
PC1: nc -lk 12345 -vn
PC2: nc 192.168.1.1 12345 -vn

Explain packet-in and packet-out in code.
