import threading
import queue
import json
import logging
from p4utils.utils.helper import load_topo
from p4utils.utils.sswitch_p4runtime_API import SimpleSwitchP4RuntimeAPI

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
        logging.info(f"Connecting to switch {sw_name}, \
                IP {sw_data['grpc_ip']}, grpc port {grpc_port}")
        self.controller = SimpleSwitchP4RuntimeAPI(device_id,
                                                   grpc_port,
                                                   grpc_ip=sw_data['grpc_ip'],
                                                   p4rt_path=p4rt_path,
                                                   json_path=json_path)
                                                   #p4rt_path=sw_data['p4rt_path'],
                                                   #json_path=sw_data['json_path'])

        self.q = queue.Queue()
        self.init()
        #self.fill_table_test()

    def config_digest(self):
        # Up to 10 digests can be sent in a single message. Max timeout set to 1 ms.
        self.controller.digest_enable('learn_t', 1000000, 10, 1000000)

    def reset(self):
        # Reset grpc server
        self.controller.reset_state()

    def init(self):
        self.reset()

    def fill_table_test(self):
        self.controller.table_add("dmac", "forward", ['00:00:0a:00:00:01'], ['1'])
        self.controller.table_add("dmac", "forward", ['00:00:0a:00:00:02'], ['2'])

    def unpack_digest(self, dig_list):
        learning_data = []
        for dig in dig_list.data:
            mac_addr = int.from_bytes(dig.struct.members[0].bitstring, byteorder='big')
            ingress_port = int.from_bytes(dig.struct.members[1].bitstring, byteorder='big')
            learning_data.append((mac_addr, ingress_port))
        return learning_data

    def recv_msg_digest(self, dig_list):
        learning_data = self.unpack_digest(dig_list)
        self.q.put(learning_data) 
        print("sw %s, q = %s"%(self.sw_name, self.q))

    def run(self):
        self.config_digest()
        while True:
            dig_list = self.controller.get_digest_list()
            self.recv_msg_digest(dig_list)
