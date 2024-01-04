__author__ = 'Cuong Tran'
__email__ = 'cuongtran@mnm-team.org'
__licence__ = 'GPL2.0'

'''
__version__ = '1.0' 202401

'''

import logging
import json

from dataclasses import dataclass
import ipaddress

from p4utils.utils.topology import NetworkGraph
from p4utils.utils.helper import load_topo

logging.basicConfig(level=logging.DEBUG, format='%(message)s')

CONFIG = json.load(open("config.json"))
TOPO = CONFIG['topo']
NET = load_topo(TOPO)
PORT_ANY='1..20'

@dataclass
class Network():
    ip: str
    mask: int

    @staticmethod
    def split_network(ip_address: str):
        """Splits a given ip_address in its two parts.
        If the address is not in the CIDR format /32 is assumed.

        192.168.178.1/32 -> (192.168.178.1, 32)
        """
        try:
            ip, cidr = ip_address.split('/')
        except ValueError:
            ip, cidr = ip_address, 32
        return Network(ip, int(cidr))

def convert_to_range(str_in: str, start=0, to=255):
    if str(str_in).lower() == "any":
        return f"{start}..{to}"
    elif '..' in str_in:
        return str(str_in).replace(" ", "")
    else:
        return f"{str_in}..{str_in}"


def range_to_exact(str_range: str):
    if '..' in str_range:
        from_, to = map(int, str_range.split('..'))
        return str(from_) if from_ == to else None

    try:
        return str(int(str_range))
    except ValueError:
        return None


def find_hosts_in_topo(src_ip: str, dst_ip: str) -> (NetworkGraph, str, str):
    src_ip = Network.split_network(src_ip).ip
    dst_ip = Network.split_network(dst_ip).ip
    host_src = None
    host_dst = None
    for (host_name, host_attrs) in NET.nodes(data=True):
        if not NET.isSwitch(host_name):
            if host_attrs['ip'] == src_ip:
                host_src = host_name
            elif host_attrs['ip'] == dst_ip:
                host_dst = host_name
        if host_src and host_dst:
            break
    return host_src, host_dst

def convert_ip_to_ter(ip_address: Network) -> str:
    if ip_address.ip.lower() == "any":
        return "0&&&0"
    else:
        host_bits = 32 - ip_address.mask
        netmask = (1 << 32) - (1 << host_bits)
        return f"{ip_address.ip}&&&{netmask}"

def is_subset(tup1, tup2):
    '''
    tup1: input tuple extracted from a packet: in_port, ip_src, ip_dst, ip_proto, l4_src, l4_dst
    tup2: tuple in the policy database, most value are range: 
    in_port range, ip_src range, ip_dst range, l4_src range, l4_dst range
    E.g., tup1 = (2, 172.16.1.1, 172.16.1.5, 6, 12345, 80)
          tup2 = (1..100, 172.16.1.1/32, 172.16.1.6/30, 1..51, 1000..10000, 80..80)
          In this case, tup1 is a subset of tup2, this function return true
    Return: True if tup1 is a subset of tup2, False otherwise
    '''
    in_port = tup2[0]
    if ".." not in in_port:
        in_port = in_port+".."+in_port
    a, b = map(int, in_port.split('..'))
    if a <= tup1[0] <= b: # compare in_port
        if (ipaddress.ip_address(tup1[1]) in ipaddress.ip_network(tup2[1], False)) and (ipaddress.ip_address(tup1[2]) in ipaddress.ip_network(tup2[2], False)): # compare ip
            proto_range = tup2[3]
            if ".." not in proto_range:
                proto_range = proto_range+".."+proto_range
            a, b = map(int, proto_range.split('..'))
            if a <= tup1[3] <= b: # compare ip_protocol
                if tup1[4] == tup1[5] == None:
                    return True
                a, b = map(int, tup2[4].split('..'))
                if a <= tup1[4] <=b: # compare l4_src
                    a, b = map(int, tup2[5].split('..'))
                    if a <= tup1[5] <= b: # compare l4_dst
                        return True
    return False
