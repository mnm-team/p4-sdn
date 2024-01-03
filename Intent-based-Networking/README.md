# Intent-based Networking

The network topology used in this example:

![network topology](topo.svg)

The previous examples: [simple\_demo](../simple_demo), [simple\_switch](../simple_switch) and [ARPcache](../ARPcache) should be made familiar in order to understand this one.


## Implementation


## Execution

Compiling the P4 code:
```
p4c-bm2-ss --p4v 16 --p4runtime-files build/ibn_sw.p4info.txt -o build/ibn_sw.json ibn_sw.p4
```

Making switches S1, S2, S3 become P4-switches, the command below applies for switch S1 (see [simple\_demo](../simple_demo) for detailed description of the options): 
```
sudo simple_switch_grpc -i 1@eth1 -i 2@eth2 -i 3@eth3 --pcap pcaps --nanolog ipc:///tmp/s1-log.ipc --device-id 1 build/ibn_sw.json --log-console --thrift-port 9090 -- --grpc-server-addr 0.0.0.0:50051 --cpu-port 255
```
It is important to specify the CPU-port to be the same port declared in the P4 code (file `ibn_sw.p4`), being 255 in this case.

Executing the controller program:
```
python ibn_api.py
```

Generating traffic between end-points, e.g., using ping:

PC1: `ping 192.168.1.2`
