__author__ = 'Cuong Tran'
__email__ = 'cuongtran@mnm-team.org'
__licence__ = 'GPL2.0'

'''
__version__ = '1.0' 202312

'''

import struct
import threading
import queue
from p4utils.utils.helper import load_topo
from p4utils.utils.sswitch_p4runtime_API import SimpleSwitchP4RuntimeAPI
import json

CONFIG = json.load(open("config.json"))

p4rt_path=CONFIG['p4rt_path']
json_path=CONFIG['json_path']
TOPO = CONFIG['topo']

class APPCore(threading.Thread):

    def __init__(self, sw_name):
        threading.Thread.__init__(self)
        self.topo = load_topo(TOPO)
        self.sw_name = sw_name
        device_id = self.topo.get_p4switch_id(sw_name)
        grpc_port = self.topo.get_grpc_port(sw_name)
        sw_data = self.topo.get_p4rtswitches()[sw_name]
        print("Connecting to switch %s, IP %s, grpc port %s"%(sw_name,sw_data['grpc_ip'],grpc_port))
        self.controller = SimpleSwitchP4RuntimeAPI(device_id, grpc_port, grpc_ip=sw_data['grpc_ip'],
                                                   p4rt_path=p4rt_path,
                                                   json_path=json_path)
                                                   #p4rt_path=sw_data['p4rt_path'],
                                                   #json_path=sw_data['json_path'])
        self.q = queue.Queue()
        self.init()

    def reset(self):
        # Reset grpc server
        self.controller.reset_state()

    def init(self):
        self.reset()

    def fill_table_test(self):
        self.controller.table_add("dmac", "forward", ['00:00:0a:00:00:01'], ['1'])
        self.controller.table_add("dmac", "forward", ['00:00:0a:00:00:02'], ['2'])

    def receive_packet_in(self):
        self.q = self.controller.sniff_packet_in()
        print("sw %s, q = %s"%(self.sw_name,self.q))

    def run(self):
        print("packet-in thread for switch %s"%self.sw_name)
        self.receive_packet_in()
