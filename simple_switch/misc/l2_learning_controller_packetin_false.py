from scapy.all import Ether
import threading
import queue
import time
import json
import logging
logging.basicConfig(level=logging.DEBUG, format='%(message)s')

from appcore import APPCore

from p4utils.utils.helper import load_topo
from p4utils.utils.sswitch_p4runtime_API import SimpleSwitchP4RuntimeAPI

CONFIG = json.load(open("config.json"))
switches=CONFIG["switches"]
TOPO=CONFIG['topo']


class L2_Learning(threading.Thread):
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
        self.q = {1:self.con[1].q, 2:self.con[2].q, 3: self.con[3].q}
        self.add_boadcast_groups()

    def add_boadcast_groups(self):
        for i,sw in enumerate(switches, start=1):
            interfaces_to_port = self.topo.get_node_intfs(fields=['port'])[sw].copy()
            print(i,sw)
            print(interfaces_to_port)
            mc_grp_id = 1
            for ingress_port in interfaces_to_port.values():
                port_list = list(interfaces_to_port.values())
                del(port_list[port_list.index(ingress_port)])
                port_list.append(255)
                print(port_list)

                # Add multicast group and ports
                self.con[i].controller.mc_mgrp_create(mc_grp_id, port_list)

                # Fill broadcast table
                self.con[i].controller.table_add("broadcast", "set_mcast_grp", [str(ingress_port)], [str(mc_grp_id)])
                mc_grp_id +=1
	#self.con[1].controller.mc_mgrp_create(1, [2,3])
        #self.con[1].controller.mc_mgrp_create(2, [1,3])
        #self.con[1].controller.mc_mgrp_create(3, [1,2])
        #self.con[1].controller.table_add("broadcast", "set_mcast_grp", ['1'], ['1'])
        #self.con[1].controller.table_add("broadcast", "set_mcast_grp", ['2'], ['2'])
        #self.con[1].controller.table_add("broadcast", "set_mcast_grp", ['3'], ['3'])
        #self.con[2].controller.mc_mgrp_create(1, [2])
        #self.con[2].controller.mc_mgrp_create(2, [1])
        #self.con[2].controller.table_add("broadcast", "set_mcast_grp", ['1'], ['1'])
        #self.con[2].controller.table_add("broadcast", "set_mcast_grp", ['2'], ['2'])
        #self.con[3].controller.mc_mgrp_create(1, [2])
        #self.con[3].controller.mc_mgrp_create(2, [1])
        #self.con[3].controller.table_add("broadcast", "set_mcast_grp", ['1'], ['1'])
        #self.con[3].controller.table_add("broadcast", "set_mcast_grp", ['2'], ['2'])

    def process_packet_in(self):
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
                    eth_src = pkt[Ether].src
                    eth_dst = pkt[Ether].dst
                    logging.debug(f"switch = {sw}, in_port = {in_port}, l2_src = {eth_src}, l2_dst = {eth_dst}")
                    self.con[sw].controller.table_add("smac", "NoAction", [str(eth_src)])
                    self.con[sw].controller.table_add("dmac", "forward", [str(eth_src)], [str(in_port)])


    def run(self):
        self.process_packet_in()


if __name__ == "__main__":
    obj = L2_Learning()
    obj.start()
