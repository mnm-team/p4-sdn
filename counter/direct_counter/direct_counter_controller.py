__author__ = 'Cuong Tran'
__email__ = 'cuongtran@mnm-team.org'
__licence__ = 'GPL2.0'

'''
__version__ = '1.0' 202401

'''


import struct
from scapy.all import ARP, Ether
import threading
import queue
import time
import json
import logging
logging.basicConfig(level=logging.DEBUG, format='%(message)s')

from p4.config.v1 import p4info_pb2
from ipaddr import IPv4Address, AddressValueError

from appcore import APPCore

from p4utils.utils.helper import load_topo
from p4utils.utils.sswitch_p4runtime_API import SimpleSwitchP4RuntimeAPI

CONFIG = json.load(open("config.json"))
switches=CONFIG["switches"]
TOPO=CONFIG['topo']

PERIOD = 3 #period in which the counter is read and if necessary, throughput is inferred

class ARPCache(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.con = {idx:APPCore(sw) for idx, sw in enumerate(switches, start=1)}
        self.q = None
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
        #test packet-out
        #pkt=Ether(dst='ff:ff:ff:ff:ff:ff')/Raw(load='Hello P4-SDN!')
        #self.con[1].controller.packet_out(bytes(pkt),'2')
        #logging.debug("Packet out sent for swich S1!")

    def process_packet_in(self):
        while True:
            for (sw, qu) in self.q.items(): #switch, queue
                #logging.debug("sw = %s, qu = %s"%(sw,qu))
                # this sleeping is to reduce the CPU occupation of this thread,
                # otherwise, cpu usage is almost always 99%
                time.sleep(0.1) 
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

    def run(self):
        self.process_packet_in()

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


    def read_direct_counter(self):
        table_name = 'dmac'
        swid = 1 # read the direct counter of table dmac (destination MAC) of switch 1
        while True:
            #self.con[1].controller.dump_table('dmac')
            entries, default_entry = self.con[swid].controller.read_all_table_entries(table_name)
            #print(f"Table {table_name} contains {len(entries)} entries")
            #for e in entries:
            #    print(e)
            #print(f"Table {table_name}'s default entry:")
            #print(default_entry)

            mfs = self.con[swid].controller.context.get_table(table_name).match_fields #mfs: match fields
            num = 1
            for e in entries:
                normal_match = [] #normal match format to be fed in the function direct_counter_read
                nmf = None # normal match field
                #print(e)
                match = e.match
                #action = e.action
                priority = e.priority
                #print(f"match = {match}")
                #print(f"action = {action}")
                #print(f"priority = {priority}")
                #print(match._mk)
                #print(match._mk.keys())
                #print(match._mk.values())
                for mf in match._mk.values(): #match field
                    #print(mf)
                    #print(f"field_id = {mf.field_id}")
                    #print(f"value = {mf.exact.value}")
                    fid = mf.field_id
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
                #print(f"final match = {normal_match}")

                res = self.con[swid].controller.direct_counter_read('rule_counter', normal_match, priority)
                print(f"Rule {num}: {e}Byte count: {res[0]}, packet count: {res[1]}\n")
                num += 1

            print("=============================================================")
            time.sleep(PERIOD)


if __name__ == "__main__":
    obj = ARPCache()
    obj.start()
    obj.read_direct_counter()
