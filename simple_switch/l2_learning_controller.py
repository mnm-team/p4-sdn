__author__ = 'Cuong Tran'
__email__ = 'cuongtran@mnm-team.org'
__licence__ = 'GPL2.0'

'''
__version__ = '1.0' 202312

'''


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
            mc_grp_id = 1
            for ingress_port in interfaces_to_port.values():
                port_list = list(interfaces_to_port.values())
                del(port_list[port_list.index(ingress_port)])
                # Add multicast group and ports
                self.con[i].controller.mc_mgrp_create(mc_grp_id, port_list)
                # Fill broadcast table
                self.con[i].controller.table_add("broadcast", "set_mcast_grp", [str(ingress_port)], [str(mc_grp_id)])
                mc_grp_id +=1

    def process_digest_messages(self):
        while True:
            for (sw, qu) in self.q.items(): #switch, queue
                #logging.debug("sw = %s, qu = %s"%(sw,qu))
                # this sleeping is to reduce the CPU occupation of this thread,
                # otherwise, cpu usage is almost always 99%
                time.sleep(0.05) 
                if not qu.empty():
                    learning_data = qu.get()
                    for mac_addr, ingress_port in  learning_data:
                        print("mac: %012X ingress_port: %s " % (mac_addr, ingress_port))
                        self.con[sw].controller.table_add("smac", "NoAction", [str(mac_addr)])
                        self.con[sw].controller.table_add("dmac", "forward", [str(mac_addr)], [str(ingress_port)])

    def run(self):
        self.process_digest_messages()


if __name__ == "__main__":
    obj = L2_Learning()
    obj.start()
