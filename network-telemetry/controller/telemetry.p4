/*
__author__ = 'Cuong Tran'
__email__ = 'cuongtran@mnm-team.org'
__licence__ = 'GPL2.0'
__version__ = '1.0' 202312
*/

/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

//compile the packetinout.p4 file by: p4c-bm2-ss --p4v 16 --p4runtime-files packetinout.p4info.txt -o packetinout.json packetinout.p4

#define CPU_PORT 255
// then start p4_switch by: sudo simple_switch_grpc -i 1@eth1 -i 2@eth2 -i 3@eth3 -i 4@eth4 --pcap pcaps --nanolog ipc:///tmp/s1-log.ipc --device-id 1 build/packetout.json --log-console --thrift-port 9090 -- --grpc-server-addr 0.0.0.0:50051 --cpu-port 255  (the cpu-port in the start command must be the same, as it is the parse value in the function MyParser below)

const bit<16> TYPE_IPV4 = 0x800;
const bit<16> TYPE_ARP = 0x806;
const bit<16> TYPE_PROBE = 0x812;

#define MAX_HOPS 10
#define MAX_PORTS 8

/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;

typedef bit<48> time_t;

struct meta_t {
    bit<1>  do_forward;
    bit<32> ipv4_sa;
    bit<32> ipv4_da;
    bit<16> l4_sp; //layer 4's source port
    bit<16> l4_dp; //layer 4's destination port
    bit<32> nhop_ipv4;
    bit<32> if_ipv4_addr;
    bit<48> if_mac_addr;
    bit<1>  is_ext_if;
    bit<16> l4Length; //layer 4's length
    bit<8>  if_index;
}

header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}

//ref: http://csie.nqu.edu.tw/smallko/sdn/LBP4.htm
header arp_t {
    bit<16> htype;
    bit<16> ptype;
    bit<8>  hlen;
    bit<8>  plen;
    bit<16> opcode;
    bit<48> hwSrcAddr;
    bit<32> protoSrcAddr;
    bit<48> hwDstAddr;
    bit<32> protoDstAddr;
}

header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<8>    diffserv;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdrChecksum;
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
}

header tcp_t {
    bit<16> srcPort;
    bit<16> dstPort;
    bit<32> seqNo;
    bit<32> ackNo;
    bit<4>  dataOffset;
    bit<4>  res;
    bit<8>  flags;
    bit<16> window;
    bit<16> checksum;
    bit<16> urgentPtr;
}

header udp_t {
    bit<16> srcPort;
    bit<16> dstPort;
    bit<16> length_;
    bit<16> checksum;
}

struct learn_t {
    bit<48> srcAddr;
    bit<9>  ingress_port;
}

// Top-level probe header, indicates how many hops this probe
// packet has traversed so far.
header probe_t {
    bit<8> hop_cnt;
}

// The data added to the probe by each switch at each hop.
header probe_data_t {
    bit<1> bos;
    bit<7> swid;
    bit<8> port;
    bit<32> byte_cnt;
    time_t last_time;
    time_t cur_time;
}

// Indicates the egress port the switch should send this probe
// packet out of. There is one of these headers for each hop.
header probe_fwd_t {
    bit<8>  egress_spec;
}

struct parser_metadata_t {
    bit<8> remaining;
}

struct metadata {
    /* empty */
    learn_t learn;
    @name(".meta")
    meta_t  meta;
    bit<8> egress_spec;
    parser_metadata_t parser_metadata;
}

@controller_header("packet_in")
header packet_in_header_t {
    bit<9>  ingress_port;
    bit<7>      _pad;
//source: https://github.com/opennetworkinglab/ngsdn-tutorial/blob/advanced/solution/p4src/main.p4
}

@controller_header("packet_out")
header packet_out_header_t {
    bit<9> egress_port; // egress_port is 9-bit wide
    //bit<16> egress_port;
    bit<7>      _pad; //padding
//source: https://github.com/opennetworkinglab/ngsdn-tutorial/blob/advanced/solution/p4src/main.p4
}


struct headers {
    packet_out_header_t packet_out;
    packet_in_header_t packet_in;
    @name(".ethernet")
    ethernet_t   ethernet;
    @name(".arp")
    arp_t arp;
    @name(".ipv4")
    ipv4_t     ipv4;
    @name(".tcp")
    tcp_t      tcp;
    @name(".udp")
    udp_t      udp;
    probe_t probe;
    probe_data_t[MAX_HOPS] probe_data;
    probe_fwd_t[MAX_HOPS] probe_fwd;
}


/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/

parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    state start {
        //transition parse_ethernet;
        transition select(standard_metadata.ingress_port) {
            CPU_PORT: parse_packet_out;
            default: parse_ethernet;
        }
    }

    state parse_packet_out {
        packet.extract(hdr.packet_out);
        transition parse_ethernet;
    }


    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            TYPE_ARP: parse_arp;
            TYPE_IPV4: parse_ipv4;
            TYPE_PROBE: parse_probe;
            default: accept;
        }
    }

    @name(".parse_arp") state parse_arp {
        packet.extract(hdr.arp);
        transition accept;
    }

    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        meta.meta.ipv4_sa = hdr.ipv4.srcAddr;
        meta.meta.ipv4_da = hdr.ipv4.dstAddr;
        meta.meta.l4Length = hdr.ipv4.totalLen - 16w20;
        transition select(hdr.ipv4.protocol) {
            8w6: parse_tcp;
            8w17: parse_udp;
            default: accept;
        }
        //transition accept;
    }

    @name(".parse_tcp") state parse_tcp {
        packet.extract(hdr.tcp);
        meta.meta.l4_sp = hdr.tcp.srcPort;
        meta.meta.l4_dp = hdr.tcp.dstPort;
        transition accept;
    }
    @name(".parse_udp") state parse_udp {
        packet.extract(hdr.udp);
        transition accept;
    }

    state parse_probe {
        packet.extract(hdr.probe);
        meta.parser_metadata.remaining = hdr.probe.hop_cnt + 1;
        transition select(hdr.probe.hop_cnt){
            0: parse_probe_fwd;
            default: parse_probe_data;
        }
    }

    state parse_probe_data {
        packet.extract(hdr.probe_data.next);
        transition select(hdr.probe_data.last.bos){
            1: parse_probe_fwd;
            default: parse_probe_data;
        }
    }

    state parse_probe_fwd {
        packet.extract(hdr.probe_fwd.next);
        meta.parser_metadata.remaining = meta.parser_metadata.remaining - 1;
        //extract the forwarding data
        meta.egress_spec = hdr.probe_fwd.last.egress_spec;
        transition select(meta.parser_metadata.remaining) {
            0: accept;
            default: parse_probe_fwd;
        }
    }

}


/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {
    apply {  }
}


/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {

    action drop() {

        mark_to_drop(standard_metadata);
    }

    table sec {
        key = {
            //hdr.ethernet.srcAddr: exact;
            hdr.ipv4.srcAddr: exact;
            hdr.ipv4.dstAddr: exact;
        }

        actions = {
            drop;
            NoAction;
        }
        size = 256;
        default_action = drop();
    }

    action mac_learn(){
        meta.learn.srcAddr = hdr.ethernet.srcAddr;
        meta.learn.ingress_port = standard_metadata.ingress_port;
        digest<learn_t>(1, meta.learn);
    }

    action send_to_cpu() {
        standard_metadata.egress_spec = CPU_PORT;
    }

    table smac {

        key = {
            hdr.ethernet.srcAddr: exact;
        }

        actions = {
            //mac_learn;
            send_to_cpu;
            NoAction;
        }
        size = 256;
        default_action = send_to_cpu;
        //default_action = mac_learn;
    }

    action forward(bit<9> egress_port) {
        standard_metadata.egress_spec = egress_port;
    }

    table dmac {
        key = {
            hdr.ethernet.dstAddr: exact;
        }

        actions = {
            forward;
            send_to_cpu;
            NoAction;
        }
        size = 256;
        default_action = send_to_cpu;
        //default_action = NoAction;
    }

    action set_mcast_grp(bit<16> mcast_grp) {
        standard_metadata.mcast_grp = mcast_grp;
    }

    table broadcast {
        key = {
            standard_metadata.ingress_port: exact;
        }

        actions = {
            set_mcast_grp;
            NoAction;
        }
        size = 256;
        default_action = NoAction;
    }

    apply {

        if (hdr.packet_out.isValid()) {
            // Implement logic such that if this is a packet-out from the
            // controller:
            // 1. Set the packet egress port to that found in the cpu_out header
            // 2. Remove (set invalid) the cpu_out header
            // 3. Exit the pipeline here (no need to go through other tables

            standard_metadata.egress_spec = hdr.packet_out.egress_port;
            hdr.packet_out.setInvalid();
            exit;
        }

        if (smac.apply().hit){
            dmac.apply();
        } 

        //if (!hdr.arp.isValid() && !sec.apply().hit) {
        //    //
        //}
        //else {
        //    smac.apply();
        //    dmac.apply();
        //    //if (dmac.apply().hit){
        //    //    //
        //    //}
        //    //else {
        //    //    broadcast.apply();
        //    //}
        //}
        if (hdr.probe.isValid()) {
            standard_metadata.egress_spec = (bit<9>)meta.egress_spec;
            hdr.probe.hop_cnt = hdr.probe.hop_cnt + 1;
        }
    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {

    // count the number of bytes seen since the last probe
    register<bit<32>>(MAX_PORTS) byte_cnt_reg;
    // remember the time of the last probe
    register<time_t>(MAX_PORTS) last_time_reg;
    
    action set_swid(bit<7> swid) {
        hdr.probe_data[0].swid = swid;
    }
    
    table swid {
        actions = {
            set_swid;
            NoAction;
        }
        default_action = NoAction();
    }


    apply { 
        if (standard_metadata.egress_port == CPU_PORT) {
            // Implement logic such that if the packet is to be forwarded to the
            // CPU port, e.g., if in ingress we matched on the ACL table with
            // action send/clone_to_cpu...
            // 1. Set cpu_in header as valid
            // 2. Set the cpu_in.ingress_port field to the original packet's
            //    ingress port (standard_metadata.ingress_port).

            hdr.packet_in.setValid();
            hdr.packet_in.ingress_port = standard_metadata.ingress_port;
            exit;
        }

        bit<32> byte_cnt;
        bit<32> new_byte_cnt;
        time_t last_time;
        time_t cur_time = standard_metadata.egress_global_timestamp;
        // increment byte cnt for this packet's port
        byte_cnt_reg.read(byte_cnt, (bit<32>)standard_metadata.egress_port);
        byte_cnt = byte_cnt + standard_metadata.packet_length;
        // reset the byte count when a probe packet passes through
        new_byte_cnt = (hdr.probe.isValid()) ? 0 : byte_cnt;
        byte_cnt_reg.write((bit<32>)standard_metadata.egress_port, new_byte_cnt);
        
        if (hdr.probe.isValid()) {
            // fill out probe fields
            hdr.probe_data.push_front(1);
            hdr.probe_data[0].setValid();
            if (hdr.probe.hop_cnt == 1) {
                hdr.probe_data[0].bos = 1;
            }
            else {
                hdr.probe_data[0].bos = 0;
            }
            // set switch ID field
            swid.apply();
            hdr.probe_data[0].port = (bit<8>)standard_metadata.egress_port;
            hdr.probe_data[0].byte_cnt = byte_cnt;
            // read / update the last_time_reg
            last_time_reg.read(last_time, (bit<32>)standard_metadata.egress_port);
            last_time_reg.write((bit<32>)standard_metadata.egress_port, cur_time);
            hdr.probe_data[0].last_time = last_time;
            hdr.probe_data[0].cur_time = cur_time;
        }

    }
}

/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers hdr, inout metadata meta) {
     apply {
	update_checksum(
	    hdr.ipv4.isValid(),
            { hdr.ipv4.version,
	      hdr.ipv4.ihl,
              hdr.ipv4.diffserv,
              hdr.ipv4.totalLen,
              hdr.ipv4.identification,
              hdr.ipv4.flags,
              hdr.ipv4.fragOffset,
              hdr.ipv4.ttl,
              hdr.ipv4.protocol,
              hdr.ipv4.srcAddr,
              hdr.ipv4.dstAddr },
            hdr.ipv4.hdrChecksum,
            HashAlgorithm.csum16);
        //update_checksum_with_payload(true, { hdr.ipv4.srcAddr, hdr.ipv4.dstAddr, 8w0, hdr.ipv4.protocol, meta.meta.l4Length, hdr.tcp.srcPort, hdr.tcp.dstPort, hdr.tcp.seqNo, hdr.tcp.ackNo, hdr.tcp.dataOffset, hdr.tcp.res, hdr.tcp.flags, hdr.tcp.window, hdr.tcp.urgentPtr }, hdr.tcp.checksum, HashAlgorithm.csum16);
        update_checksum_with_payload(hdr.tcp.isValid(), { hdr.ipv4.srcAddr, hdr.ipv4.dstAddr, 8w0, hdr.ipv4.protocol, meta.meta.l4Length, hdr.tcp.srcPort, hdr.tcp.dstPort, hdr.tcp.seqNo, hdr.tcp.ackNo, hdr.tcp.dataOffset, hdr.tcp.res, hdr.tcp.flags, hdr.tcp.window, hdr.tcp.urgentPtr }, hdr.tcp.checksum, HashAlgorithm.csum16);
        update_checksum_with_payload(hdr.udp.isValid(), { hdr.ipv4.srcAddr, hdr.ipv4.dstAddr, 8w0, hdr.ipv4.protocol, meta.meta.l4Length, hdr.udp.srcPort, hdr.udp.dstPort, hdr.udp.length_ }, hdr.udp.checksum, HashAlgorithm.csum16);
    }
}


/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        //parsed headers have to be added again into the packet.
        packet.emit(hdr.packet_in);
        packet.emit(hdr.ethernet);
        packet.emit(hdr.arp);
        packet.emit(hdr.ipv4);
        packet.emit(hdr.tcp);
        packet.emit(hdr.udp);
        packet.emit(hdr.probe);
        packet.emit(hdr.probe_data);
        packet.emit(hdr.probe_fwd);
    }
}

/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

//switch architecture
V1Switch(
MyParser(),
MyVerifyChecksum(),
MyIngress(),
MyEgress(),
MyComputeChecksum(),
MyDeparser()
) main;

