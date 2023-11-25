from p4utils.utils.helper import load_topo
from p4utils.utils.sswitch_p4runtime_API import SimpleSwitchP4RuntimeAPI
import logging
logging.basicConfig(level=logging.DEBUG, format='%(message)s')


topo = load_topo('topo_simple_demo.json')
controllers = {}

for switch, data in topo.get_p4rtswitches().items():
    logging.debug("Connecting to switch %s, IP %s, grpc port %s"%(switch,data['grpc_ip'],data['grpc_port']))
    controllers[switch] = SimpleSwitchP4RuntimeAPI(data['device_id'], data['grpc_port'],
                                                  grpc_ip=data['grpc_ip'],
                                                  p4rt_path=data['p4rt_path'],
                                                  json_path=data['json_path'])

con = {1:controllers['s1'], 2:controllers['s2']}

# Reset grpc server
con[1].reset_state()
con[2].reset_state()

# clear existing rules in switches s1 and s2
con[1].table_clear('table_forwarding')
con[2].table_clear('table_forwarding')

# add rules in switch s1
con[1].table_add('table_forwarding', 'forward', ['1'], ['2'])
con[1].table_add('table_forwarding', 'forward', ['2'], ['1'])

# add rules in switch s22
con[2].table_add('table_forwarding', 'forward', ['1'], ['2'])
con[2].table_add('table_forwarding', 'forward', ['2'], ['1'])
