In traditional networks, the control plane and data plane are tightly bundled in a network device. For example, the OSPF routing protocol (control plane) populates the routing table (data plane) in a router, each router has its own OSPF instance, these instances communicate with each other (via the connections between routers in the data plane) to have the global information of the network domain that they influence. 
This networking approach of distributed control plane facilitates the fast growth of a network (and the big Internet), however, it also largely  hinders network innovation. The control plane can only be defined, programmed, changed by network vendors, end-users can only enable, disable or configure some existing features on network devices, but cannot add or program a new function. The process of requesting a new feature from end-users to network vendors often takes months or years (see [SDN: the new norm for networks](https://opennetworking.org/wp-content/uploads/2011/09/wp-sdn-newnorm.pdf))


The approach of Software-defined Networking is to decouple the control plane from the data plane into a (logically) remote and centralized entity, and introduce a common open API for the communication between these two planes. This design facilitates the programming of the data plane and promotes network innovation. A user can experiment new network functions via programming the network by himself without having to wait for the implementation from network vendors. We contrast the difference between the two networking approaches in the picture below.

<img src="traditionalnetworkvssdn.svg" alt="traditional network vs SDN" width="150%"/>


