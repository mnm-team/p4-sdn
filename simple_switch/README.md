# Implementing simple l2-learning switch with P4

This imitates the behaviour of a normal traditional switch: upon receiving a packet, the switch looks at its destination MAC address, if there is no matching rule in its switching table, the switch flood that packet on all ports except for the incoming port. The switch also notice the source address, say `MAC-addr`, the incoming port, say `P`, and add a corresponding rule to its switching table: if the destination MAC address of a packet is `MAC-addr`, then send it out of port `P`.

The switch does not work properly in a network topology containing loops. To tackle this, we implement another P4 program and controller application, namely [ARPcache](../ARPcache), that can function in that case.

This implementation is based on the L2\_Learning's implementation from nsg-ethz networking group (https://github.com/nsg-ethz/p4-learning/tree/master/exercises/04-L2_Learning/p4runtime)

The explanation to controller functions can be found at: https://nsg-ethz.github.io/p4-utils/p4utils.utils.sswitch_p4runtime_API.html

The digest method is explained at https://p4.org/p4-spec/p4runtime/main/P4Runtime-Spec.html#sec-digest

The network topology used in this example:

![topo-noloop](topo_noloop.svg)


