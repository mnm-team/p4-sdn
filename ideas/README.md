# Ideas for further exploration with P4-based SDN

## Deploy IDPS (Intrusion detection and prevention system) in SDN with Zeek or Snort, make an example with the DoS attack.

+ The IPDS-Zeek (or Snort) service is deployed separately from the controller.

+ The boundary switch (which is the gateway) mirrors the incoming traffic from outside to the IDPS service.
  
+ Upon detecting some threat, the IDPS service will ask the controller to install rules on the gateway to drop the harmful traffic.

+ Demo with DoS attack, e.g., botnet.


## Intent-based Networking
  
+ Implementing the northbound APIs for control applications to interact with the controller, and to deploy rules automatically in P4-devices. Some northbound APIs are implemented in [Intent-based-Networking](../Intent-based-Networking), e.g., allow or deny traffic between two certain hosts. Further APIs to be realized: allow stateful connection only, rate-limiting, one-way connection...

+ Long-term (for theses): Translate high-level policies (intent) into low-level one (rules in P4-devices)

## Combining P4-based SDN and traditional networks

Testing different scenarios, e.g., a network with mixture from P4-based SDN and normal switches, normal routers, or combining two SDNs via a normal network. In the test-bed, we can use Open vSwitch for normal switches, and FRRouting for normal routers.


## Implementing MEADcast with P4

[MEADcast](https://www.iariajournals.org/security/tocv12n12.html) is a sender centric multicast scheme with awareness of privacy aspects.  In MEADcast, the management tasks are performed by the sender, leaving the recipients untouched, i.e., they don't have to be changed or take part in the management task as in traditional multicast or other multicast schemes. The more MEADcast-capable routers the network has, the more efficient the communication via MEADcast is.

As a language for programming the data plane, P4 is also an elegent option for implementing MEADcast routers.
