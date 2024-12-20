# Ideas for further exploration with P4-based SDN

## Deploy IDPS (Intrusion detection and prevention system) in SDN with Zeek or Snort, make an example with the DoS attack.

+ The IPDS-Zeek (or Snort) service is deployed separately from the controller.

+ The boundary switch (which is the gateway) mirrors the incoming traffic from outside to the IDPS service.
  
+ Upon detecting some threat, the IDPS service will ask the controller to install rules on the gateway to drop the harmful traffic.

+ Demo with DoS attack, e.g., botnet.


## Intent-based Networking
  
+ Implementing the northbound APIs for control applications to interact with the controller, and to deploy rules automatically in P4-devices. Some northbound APIs are implemented in [Intent-based-Networking](../Intent-based-Networking), e.g., allow or deny traffic between two certain hosts. Further APIs to be realized: allowing stateful connection only, rate-limiting, one-way connection, forcing certain traffic to go through a chosen point...

+ Long-term (for theses): translating high-level policies (intent) into low-level one (rules in P4-devices)

## Implementing stateful firewall

Once a stateful connection is specified from A to B, A can initiate the communication and B will respond, the firewall allows this. The firewall does not allow B to initiate the communication.

A simple example using Bloom filter can be found here: https://github.com/nsg-ethz/p4-learning/tree/master/examples/stateful_firewall

## Implementing BGP with P4

Similar to the implementation of OSPF with P4: https://github.com/fno2010/pwospf-p4/

Testing: an Autonomous System (AS)  with OSPF (using FRRouting) "talks" with another P4-based AS via BGP.

## Combining P4-based SDN and traditional networks

Testing different scenarios, e.g., a network with mixture from P4-based SDN and normal switches, normal routers, or combining two SDNs via a normal network. In the test-bed, we can use Open vSwitch for normal switches, and FRRouting for normal routers.

An example can be found at: https://github.com/nsg-ethz/p4-utils/tree/master/examples/frrouters

OSPF with P4: https://github.com/fno2010/pwospf-p4/


## Implementing MEADcast with P4

[MEADcast](https://www.iariajournals.org/security/tocv12n12.html) is a sender centric multicast scheme with awareness of privacy aspects.  In MEADcast, the management tasks are performed by the sender, leaving the recipients untouched, i.e., they don't have to be changed or take part in the management task as in traditional multicast or other multicast schemes. The more MEADcast-capable routers the network has, the more efficient the communication via MEADcast is.

As a language for programming the data plane, P4 is an elegant option for implementing MEADcast routers.


## Topology discovery

Discovering the introduction or removal of links between P4-switches based on LLDP (Link Layer Discovery Protocol) messages as described in https://volkan.yazi.ci/blog/post/2013/08/06/sdn-discovery/, and update the controller's global view of the network topology accordingly. This is useful in many cases, e.g., preventing traffic to be sent to a black-hole and being dropped without acknowledgement, due to a link being down, or calculating a new shortest path between end-points.


## NDP

Caching the mapping between IPv6 and MAC addresses. This is similar to the [ARPcache](../ARPcache) but is applicable for IPv6. ARPcache creates a mapping between IPv4 and MAC addresses of end-points.


## NAT

Implementing Network Address Translation with P4: the NAT function of a normal router will be implemented in a P4-device acting as the gateway of a network.

## VPN

Implementing Virtual Private Network (VPN) with P4.

## Redesigning the Internet

The Internet was not designed with security in mind (ARPANET), it grows into an unmanageable size with lots of complexity and problems, then solutions are proposed making it even more complex. If it were designed with all the today's problems (security, privacy...) in consideration...
