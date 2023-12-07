# Implementing simple l2-learning switch with P4

This imitates the behaviour of a normal traditional switch: upon receiving a packet, the switch looks at its destination MAC address, if there is no matching rule in its switching table, the switch flood that packet on all ports except for the incoming port. The switch also notice the source address, say `MAC-addr`, the incoming port, say `P`, and add a corresponding rule to its switching table: if the destination MAC address of a packet is `MAC-addr`, then send it out of port `P`.

The switch does not work properly in a network topology containing loops. To tackle this, we implement another P4 program and controller application, namely [ARPcache](../ARPcache), that can function in that case.


