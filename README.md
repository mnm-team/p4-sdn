# p4-sdn

Software-defined Networks (SDN) is a new approach for networking in contrast to traditional networks. Network control is decoupled from forwarding functions and is directly programmable in SDN, instead of being (manually) configurable as in traditional networks. [RFC7426](https://www.rfc-editor.org/rfc/rfc7426.html) delineates the key points to comprehend SDN.

We demonstrate SDN based on P4 and P4-Runtime, which are a data plane programming language and the API for communication between the control plane and the data plane, respectively (check [p4.org/specs](https://p4.org/specs/) for specifications of P4 and P4Runtime). In the past (since approx. 2010), OpenFlow tended to be the standard for SDN. Recently, OpenFlow is claimed to be replaced by P4 (see: [Clarifying the differences between P4 and OpenFlow](https://opennetworking.org/news-and-events/blog/clarifying-the-differences-between-p4-and-openflow/)).

The library of this repository, p4utils, is based on the [p4-utils](https://github.com/nsg-ethz/p4-utils) repository, which is again based on the [p4-shell](https://github.com/p4lang/p4runtime-shell) repository. We implement further APIs for the SDN controller, e.g., packet-in, packet-out, APIs related to idle timeout, and provide useful examples.

The examples are designed for the Rechnernetze Praktikum (RNP) at MNM-Team, LMU. The specification of the infrastructure and details about the course are provided in the course's script. The course are usually held annually in the winter semester (e.g., [RNP WS2023/2024](https://www.nm.ifi.lmu.de/teaching/Praktika/2023ws/rnp/)).

+ The [simple\_demo](simple_demo) example shows a simple demonstration of SDN.

+ The simple\_hub, simple\_switch examples illustrate how a normal hub and switch can be implemented by P4-based SDN.

+ As a hub or switch cannot work properly in a network topology containing loops, we show a more advanced example, arpcache, to cope with that problem.

+ The controller can measure the data throughput of a switch's port, or the number of packets matched by a certain rule in a switch.

+ In some case, we might want to remove idle rules, i.e., rules that do not match any packet for some lapse of time. The rule\_timeout example demonstrates how this can be achieved.

+ SDN boosts the adoption of policy-based network management, and recently intent-based networking. In this regard, we provide an example, in which the SDN controller exposes the useful REST APIs for controlling the data plane.
