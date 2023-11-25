# First demo of P4-based SDN

We demonstrates SDN via a simple example, showing how a controller can install rules in two switches to allow traffic between two end-points.

The network topology used in this example:
![topo-simple-demo](topo-simple-demo.svg)

## Execution

We need to compile the P4 program to obtain the P4 Device config (\*.json) and the P4Info files (\*.p4info.txt), which are to be consumed by P4 switches and controllers, respectively. 

### Compiling the P4 program:

```
p4c-bm2-ss --p4v 16 --p4runtime-files build/simple\_demo.p4info.txt -o build/simple\_demo.json simple\_demo.p4
```

### Deploying P4 switches:

We can create a P4 switch at switch S1 by the following commands:

```
simple\_switch\_grpc -i 1@eth1 -i 2@eth2 --pcap pcaps
--nanolog ipc:///log.ipc --device-id 1 simple\_demo.json
--log-console --thrift-port 9090
-- --grpc-server-addr 0.0.0.0:50051 --cpu-port 255
```

The command simple\_switch\_grpc creates a SimpleSwitchGRPC target, which is a version of SimpleSwitch with P4Runtime support (see [simple\_switch\_grpc](https://github.com/p4lang/behavioral-model/blob/main/targets/simple_switch_grpc/README.md) for more details).

+ the part `-i 1@eth1 -i 2@eth2` specifies the binding of the switch ports to
the “physical” interfaces of the (virtual) machine,
+ `--pcap pcaps`: generating pcap files for interfaces,
+ `--nanolog ipc:///log.ipc`: IPC socket to use for nanomsg pub/sub logs,
+ `--device-id 1`: device ID, used to identify the device in IPC messages,
+ `--log-console`: enabling logging on stdout,
+ `--thrift-port 9090`: TCP port on which to run the Thrift runtime server,
+ `--grpc-server-addr 0.0.0.0:50051`: bind gRPC server to the given address,
+ `--cpu-port 255`: the logical port where packet-in and packet-out comes to/from controller from/to the switch.

For more information, we can use the command `simple\_switch\_grpc --help`.

Similarly, we can create a P4 switch at switch S2:

```
simple\_switch\_grpc -i 1@eth1 -i 2@eth2 --pcap pcaps
--nanolog ipc:///log.ipc --device-id 2 simple\_demo.json
--log-console --thrift-port 9090
-- --grpc-server-addr 0.0.0.0:50051 --cpu-port 255
```

### Executing the control application

Now we can execute the control application:

```
python controller.py
```

### Testing:

We can test the communication between hosts h1 (IP: 192.168.1.1) and h2 (IP: 192.168.1.2) by the `ping` command. From host h1, do:

```
ping 192.168.1.2
```

The ping should be successful.


## Explanation

In the P4 program, we specify a table, naming `table\_forwarding`. This table has the key (match) as the `ingress port` of the incoming packet, and the actions being either `forward` or `NoAction` (do nothing), the `forward` action has the parameter `egress port`. Once deploying this P4 program in the P4 switc, the switch has a table with the rule structure that can match packets based on these defined key and actions. Note that the switch has such a table, but there is no rule in that table, except for the default rule (do nothing). At this point, the two hosts h1 and h2 cannot ping each other.

When executing the controller, it installs two rules in each switch via the `table\_add` command (see [SimpleSwitchP4RuntimeAPI](https://nsg-ethz.github.io/p4-utils/p4utils.utils.sswitch_p4runtime_API.html#p4utils.utils.sswitch_p4runtime_API.SimpleSwitchP4RuntimeAPI.table_add)). Now there are rules in the switches s1 and s2, which can handle traffic between the hosts h1 and h2.
