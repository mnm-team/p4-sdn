__author__ = 'Cuong Tran'
__email__ = 'cuongtran@mnm-team.org'
__licence__ = 'GPL2.0'

'''
__version__ = '1.0' 20240103

'''

import struct
from scapy.all import ARP, Ether
import threading
import queue
import time
import json
import logging
logging.basicConfig(level=logging.DEBUG, format='%(message)s')

from appcore import APPCore

from p4utils.utils.helper import load_topo
from p4utils.utils.sswitch_p4runtime_API import SimpleSwitchP4RuntimeAPI

from p4.config.v1 import p4info_pb2
from ipaddr import IPv4Address, AddressValueError

import ibn_util as util

CONFIG = json.load(open("config.json"))
switches=CONFIG["switches"]
TOPO=CONFIG['topo']
PRI = 2 # Priority of rules
PORT_ANY=util.PORT_ANY


class IBNApp(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.con = {idx:APPCore(sw) for idx, sw in enumerate(switches, start=1)}
        self.q = None
        self.to_noti = None # timeout notification
        self.arpdb = {} # ARP database {'IP':{'swid': swid, 'mac': MAC addr, 'port':port}} #swid: switch ID
        self.topo = load_topo(TOPO)
        self.init()

    def init(self):
        for con_i in self.con.values():
            con_i.start()
            # need this timeout so that the instantiation of the self.q
            # in the next line gets the same address source in the memory
            time.sleep(0.3) 
        self.q = {idx:self.con[idx].q for idx, sw_ in enumerate(switches, start=1)}
        self.to_noti = {idx:self.con[idx].to_noti for idx, sw_ in enumerate(switches, start=1)}

        for connection in self.con.values():
            # 100 is the cloning session defined in the p4 code (in the p4
            # switch), port 254 is for cloning packets, this port can then be
            # connected to a server for analysis, e.g. snort, or
            # zeek server.
            # These arguments have to be passed to simple_switch_grpc
            # (e.g.: -i 254@eth8)
            connection.controller.cs_create(100, [254])
        # add to table tab_mirror a rule saying only mirror allowed traffic 
        # from port facing a host, e.g., switch s1 mirrors only traffic from 
        # ports 1 (connected to PC1 in our test topo), switch s2 mirrors
        # only traffic from port 1 (connected to PC2)
        #self.con[1].controller.table_add("tab_mirror", "mirror", ["1"])
        #self.con[2].controller.table_add("tab_mirror", "mirror", ["1"])
        #self.add_test_rule()

    def add_test_rule(self):
        # only for testing encryption between pc1 and pc3 on topo_pt1
        self.con[1].controller.table_add(
            table_name="tab_ibn",
            action_name="forward",
            match_keys=[PORT_ANY,'192.168.1.1','192.168.1.2','6..6','0..65000','0..65000'],
            action_params=['2'],
            prio = PRI
        )
        self.con[1].controller.table_add(
            table_name="tab_ibn",
            action_name="forward",
            match_keys=[PORT_ANY,'192.168.1.1','192.168.1.3','6..6','0..65000','0..65000'],
            action_params=['3'],
            prio = PRI
        )
        self.con[2].controller.table_add(
            table_name="tab_ibn",
            action_name="forward",
            match_keys=[PORT_ANY,'192.168.1.2','192.168.1.1','6..6','0..65000','0..65000'],
            action_params=['2'],
            prio = PRI
        )
        self.con[2].controller.table_add(
            table_name="tab_ibn",
            action_name="forward",
            match_keys=[PORT_ANY,'192.168.1.2','192.168.1.3','6..6','0..65000','0..65000'],
            action_params=['3'],
            prio = PRI
        )
        logging.debug("Added test rules")

    def process_packet_in_and_idle_timeout_notification(self):
        while True:
            for (sw, qu) in self.q.items(): #switch, queue
                #logging.debug("sw = %s, qu = %s"%(sw,qu))
                # this sleeping is to reduce the CPU occupation of this thread,
                # otherwise, cpu usage is almost always 99%
                time.sleep(0.05) 
                if not qu.empty():
                    raw = qu.get()
                    pkt = Ether(raw.packet.payload) #pkt: packet
                    in_port = int.from_bytes(raw.packet.metadata[0].value, byteorder='big')
                    logging.debug("switch = %s, in_port = %s"%(sw,in_port))
                    if ARP in pkt:
                        arpp = pkt[ARP]
                        logging.debug("ARP OP = %s"%arpp.op)
                        logging.debug("ARP HWSRC = %s"%arpp.psrc)
                        self.update_arpdb(sw, in_port, pkt)

            for (switch1, queue1) in self.to_noti.items():
                time.sleep(0.05)
                if not queue1.empty():
                    raw = queue1.get()
                    print(f"Timeout notification: switch={switch1}, raw={raw}")
                    #print(f"{raw.idle_timeout_notification.table_entry}")
                    table_id = raw.idle_timeout_notification.table_entry[0].table_id
                    table_name = self.con[switch1].controller.context.get_name_from_id(table_id)
                    print(f"table name converted from table ID: {table_name}")
                    mfs = self.con[switch1].controller.context.get_table(table_name).match_fields
                    match = raw.idle_timeout_notification.table_entry[0].match
                    normal_match = [] #normal match format to be fed in the function table_delete_match
                    nmf = None # normal match field
                    for mf in match: #match field
                        print(mf)
                        fid = mf.field_id
                        #print(f"field ID = {mf.field_id}")
                        if mfs[fid-1].match_type == p4info_pb2.MatchField.EXACT:
                            nmf = f"{int.from_bytes(mf.exact.value, 'big')}"
                        if mfs[fid-1].match_type == p4info_pb2.MatchField.RANGE:
                            nmf = f"{int.from_bytes(mf.range.low,'big')}..{int.from_bytes(mf.range.high,'big')}"
                        if mfs[fid-1].match_type == p4info_pb2.MatchField.TERNARY:
                            try:
                                nmf = f"{IPv4Address(mf.ternary.value)}&&&{IPv4Address(mf.ternary.mask)}"
                            except AddressValueError:
                                print("Error parsing ip address from idle timeout notification")
                        if mfs[fid-1].match_type == p4info_pb2.MatchField.LPM:
                            try:
                                nmf = f"{IPv4Address(mf.lpm.prefix)}/{int.from_bytes(mf.lpm.length,'big')}"
                            except AddressValueError:
                                print("Error parsing ip address from idle timeout notification")
                        #print(f"converted match field = {nmf}")
                        normal_match.append(nmf)
                    print(f"final match = {normal_match}")
                    priority = raw.idle_timeout_notification.table_entry[0].priority
                    #print(f"priority from idle timeout notification: {priority}")
                    print(f"delete that entry")
                    self.con[switch1].controller.table_delete_match(table_name, normal_match, priority)

    def run(self):
        self.process_packet_in_and_idle_timeout_notification()

    def update_arpdb(self, swid, port, pkt):
        """
        Args:
            port: ingress_port of the packet to the switch swid, 
            pkt : Packet
        """
        logging.debug("before: self.arpdb = %s"%self.arpdb)
        sw_name = 's'+str(swid) #e.g., sw_name = 's1' 
        nb = self.topo.port_to_node(sw_name, port) #nb: neighbor
        arpp = pkt[ARP]
        if not self.topo.isHost(nb): #arpp is sent from a neighboring switch, not a host, do not process
            logging.debug("return")
            return
        if arpp.psrc not in self.arpdb:
            self.arpdb[arpp.psrc] = {'swid':swid, 'mac':arpp.hwsrc, 'port': port}
            #install rule for ARP message on the same switch
            self.con[swid].controller.table_add("smac", "NoAction", [arpp.hwsrc])
            self.con[swid].controller.table_add("dmac", "forward", [arpp.hwsrc], [str(port)])
        if arpp.op == 1:
            logging.debug("ARP Request")
            self.broadcast_arp_request_to_endpoints(swid, port, pkt)
        if arpp.op == 2:
            logging.debug("ARP Reply")
            if arpp.psrc in self.arpdb and arpp.pdst in self.arpdb:
                self.install_path_rule_for_arp_reply(swid, self.arpdb[arpp.pdst]['swid'], arpp.hwsrc, arpp.hwdst)
                logging.debug("install rules on the reverse path")
                self.install_path_rule_for_arp_reply(self.arpdb[arpp.pdst]['swid'], swid, arpp.hwdst, arpp.hwsrc)

        logging.debug("after: self.arpdb = %s"%self.arpdb)
            

    def broadcast_arp_request_to_endpoints(self, swid, port, pkt):
        """
        Broadcast ARP request in a shortcut way to avoid amplifying
        arp packets due to loops in the network. 
        Args:
            pkt: Packet, 
            swid: switch ID, 
            port: ingress port of the arp packet pkt to the switch swid
        """
        logging.debug("Broadcasting ARP Request to end-points")
        for (sw, con) in self.con.items():
            sw_name = 's'+str(sw) #e.g., sw_name = 's1'
            for nb in self.topo.get_neighbors(sw_name):#nb: neighbor
                if self.topo.isHost(nb):
                    out_port = self.topo.node_to_node_port_num(sw_name, nb)
                    if (sw, out_port) != (swid, port):
                        #do not send arp request to the ingress port of 
                        #that arp request packet
                        self.send_packet_out(sw, out_port, pkt)
    
    def send_packet_out(self, sw, port, pkt):
        self.con[sw].controller.packet_out(bytes(pkt),str(port))
        logging.debug("Packet out sent for swich %s on port %s"%(sw, port))

    def install_path_rule_for_arp_reply(self, src_sw, dst_sw, src_mac_addr, dst_mac_addr):
        logging.debug("install path rule for ARP REPLY")
        path = self.topo.get_shortest_paths_between_nodes('s'+str(src_sw),'s'+str(dst_sw))[0]
        logging.debug("shortest path between switches %s and %s is %s"%(src_sw, dst_sw, path))
        i = 1 #index
        for sw in path:
            swid = int(sw[1:]) #e.g., sw = 's10', swid = 10
            if i<len(path):
                port = self.topo.node_to_node_port_num(sw, path[i])
                self.con[swid].controller.table_add("dmac", "forward", [dst_mac_addr], [str(port)])
                self.con[swid].controller.table_add("smac", "NoAction", [src_mac_addr])
            else:#last node in the path
                self.con[swid].controller.table_add("smac", "NoAction", [src_mac_addr])
                pass #already installed the entry for dmac table when packet-in for ARP Request arrived
            i += 1


    def install_path_rule_in_ibn_table(self, in_port, l3_src, l3_dst, ip_proto, l4_src, l4_dst, path, idle_timeout=0):
        #path = self.topo.get_shortest_paths_between_nodes(l3_src, l3_dst)[0]
        #logging.debug("path = %s",path)
        match_fwd = [in_port, l3_src, l3_dst, ip_proto, l4_src, l4_dst]
        match_bck = [in_port, l3_dst, l3_src, ip_proto, l4_dst, l4_src]
        match_icmp_fwd = [in_port, l3_src, l3_dst, '1..1', '0..0', '0..0']
        match_icmp_bck = [in_port, l3_dst, l3_src, '1..1', '0..0', '0..0']

        table_action = "forward"

        for i, sw in enumerate(path[1:-1], start=2):
            sid = self.topo.nodes()[sw]['device_id'] # switch id
            port = self.topo.node_to_node_port_num(sw, path[i])
            logging.debug(f"add rule to tab_ibn of switch {sw}: {match_fwd}")
            self.con[sid].controller.table_add(
                table_name="tab_ibn",
                action_name=table_action,
                match_keys=match_fwd,
                action_params=[str(port)],
                prio = PRI,
                idle_timeout = idle_timeout
            )
            # ICMP for easy testing
            logging.debug(f"add rule to tab_ibn of switch {sw}: {match_icmp_fwd}")
            self.con[sid].controller.table_add(
                table_name="tab_ibn",
                action_name=table_action,
                match_keys=match_icmp_fwd,
                action_params=[str(port)],
                prio = PRI,
                idle_timeout = idle_timeout
            )
            # reverse path
            port = self.topo.node_to_node_port_num(sw, path[i-2]) #p[i-2] is the sw or host/server before that sw on the path p
            logging.debug(f"add rule to tab_ibn of switch {sw}: {match_bck}")
            self.con[sid].controller.table_add(
                table_name="tab_ibn",
                action_name=table_action,
                match_keys=match_bck,
                action_params=[str(port)],
                prio = PRI,
                idle_timeout = idle_timeout
            )
            # ICMP for easy testing
            logging.debug(f"add rule to tab_ibn of switch {sw}: {match_icmp_bck}")
            self.con[sid].controller.table_add(
                table_name="tab_ibn",
                action_name=table_action,
                match_keys=match_icmp_bck,
                action_params=[str(port)],
                prio = PRI,
                idle_timeout = idle_timeout
            )
            logging.debug(f"Added rules for hosts in table tab_ibn of sw {sid}")


    def delete_path_rule_in_ibn_table(self, in_port, l3_src, l3_dst, ip_proto, l4_src, l4_dst, path):
        for sw in (path[1:-1]):
            sid = self.topo.nodes()[sw]['device_id'] # switch id
            self.con[sid].controller.table_delete_match(
                    table_name=f"tab_ibn",
                    match_keys=[in_port, l3_src, l3_dst, ip_proto, l4_src, l4_dst],
                    prio=PRI)
            # delete ICMP rule
            self.con[sid].controller.table_delete_match(
                    table_name=f"tab_ibn",
                    match_keys=[PORT_ANY, l3_src, l3_dst, '1..1', '0..0', '0..0'],
                    prio=PRI)
            # reverse path
            self.con[sid].controller.table_delete_match(
                    table_name=f"tab_ibn",
                    match_keys=[in_port, l3_dst, l3_src, ip_proto, l4_dst, l4_src],
                    prio=PRI)
            # delete ICMP rule
            self.con[sid].controller.table_delete_match(
                    table_name=f"tab_ibn",
                    match_keys=[PORT_ANY, l3_dst, l3_src, '1..1', '0..0', '0..0'],
                    prio=PRI)
            logging.debug(f"Removed rules for hosts in table tab_ibn of sw {sid}")

