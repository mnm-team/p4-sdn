import logging
import json

from dataclasses import dataclass

from flask import Flask, jsonify, request
from flask_restful import Api

from p4utils.utils.topology import NetworkGraph
from p4utils.utils.helper import load_topo

from ibn_app import IBNApp

import ibn_util as util

logging.basicConfig(level=logging.DEBUG, format='%(message)s')

app = Flask(__name__)
api = Api(app)

NET = util.NET
Network = util.Network
PORT_ANY = util.PORT_ANY

# falcon controller: overall/all/boss controller that is a collection of each
# single controller of each switch
fc = IBNApp()
fc.start()

@app.route('/allow', methods=['POST'])
def add_ibn_rulepath():
    json_data = request.get_json(force=True)
    logging.debug("Call add_ibn_rulepath")

    def get_or_default(key):
        return str(json_data.get(key, "any")).strip()

    ip_src = get_or_default('src_ipv4_addr')
    ip_dst = get_or_default('dst_ipv4_addr')
    ip_proto = get_or_default('ip_proto')
    src_port = get_or_default('src_port')
    dst_port = get_or_default('dst_port')

    logging.debug(f"src_ipv4_addr={ip_src} dst_ipv4_addr={ip_dst} \
            ip_proto={ip_proto} src_port={src_port} dst_port={dst_port}")
    logging.info(f"Attempt to add a rule path between {ip_src} and {ip_dst}")

    host_src, host_dst = util.find_hosts_in_topo(ip_src, ip_dst)
    if not host_src or not host_dst:
        return jsonify(f"Input for hosts is incorrect, please check again: \
                host_src={host_src} host_dst={host_dst}")

    logging.debug(f"src={host_src}, dst={host_dst}")
    path = NET.get_shortest_paths_between_nodes(host_src, host_dst)
    logging.debug(f"path={path}")
    path = path[0]

   # preparing arguments for table tab_ibn
    # ter = ternary, the data type in the table tab_ibn in p4 code for switches
    ip_src_ter = util.convert_ip_to_ter(Network.split_network(ip_src))
    ip_dst_ter = util.convert_ip_to_ter(Network.split_network(ip_dst))

    # range is the data type in the table tab_ibn of the p4 switches
    ip_proto_range = util.convert_to_range(ip_proto)

    src_port_range = util.convert_to_range(src_port, to=65535)
    dst_port_range = util.convert_to_range(dst_port, to=65535)

    if any(['any' == v for v in [PORT_ANY, ip_src_ter, ip_dst_ter, ip_proto_range, src_port_range, dst_port_range]]):
        logging.error(f"'any' found in the matching fields:\nport: {PORT_ANY}, sip: {ip_src_ter}, dip: {ip_dst_ter}, proto: {dst_proto_range}, sport: {src_port_range}, dport: {dst_port_range}")
    else:
        logging.debug("all matching fields have been normalized")

    fc.install_path_rule_in_ibn_table(
        PORT_ANY,
        ip_src_ter,
        ip_dst_ter,
        ip_proto_range,
        src_port_range,
        dst_port_range,
        path
    )
    return jsonify("Success"), 200, {'Access-Control-Allow-Origin': '*'}


@app.route('/deny', methods=['POST'])
def del_ibn_rulepath():
    json_data = request.get_json(force=True)
    logging.debug("Call del_ibn_rulepath")

    def get_or_default(key):
        return str(json_data.get(key, "any")).strip()

    ip_src = get_or_default('src_ipv4_addr')
    ip_dst = get_or_default('dst_ipv4_addr')
    ip_proto = get_or_default('ip_proto')
    src_port = get_or_default('src_port')
    dst_port = get_or_default('dst_port')

    logging.debug(f"src_ipv4_addr={ip_src} dst_ipv4_addr={ip_dst} \
            ip_proto={ip_proto} src_port={src_port} dst_port={dst_port}")
    logging.info(f"Attempt to delete a rule path between {ip_src} and \
            {ip_dst}")

    host_src, host_dst = util.find_hosts_in_topo(ip_src, ip_dst)
    if not host_src or not host_dst:
        return jsonify(f"Input for hosts is incorrect, please check again: \
                host_src={host_src} host_dst={host_dst}")
    logging.debug(f"src={host_src}, dst={host_dst}")
    path = NET.get_shortest_paths_between_nodes(host_src, host_dst)
    logging.debug(f"path={path}")
    path = path[0]
    # preparing arguments for table tab_ibn
    # range is the data type in the table tab_ibn of the p4 switches
    # ter = ternary, the data type in p4 code for switches
    ip_src_ter = util.convert_ip_to_ter(Network.split_network(ip_src))
    ip_dst_ter = util.convert_ip_to_ter(Network.split_network(ip_dst))

    ip_proto_range = util.convert_to_range(ip_proto)

    src_port_range = util.convert_to_range(src_port, to=65535)
    dst_port_range = util.convert_to_range(dst_port, to=65535)

    fc.delete_path_rule_in_ibn_table(
        PORT_ANY,
        ip_src_ter,
        ip_dst_ter,
        ip_proto_range,
        src_port_range,
        dst_port_range,
        path
    )

    return jsonify("Success"), 200, {'Access-Control-Allow-Origin': '*'}


if __name__ == '__main__':
    print("main thread!")
    # use_reloader = False to stop Flask running itself twice, which breaks the
    # connection with the P4-switches
    # (src: https://stackoverflow.com/questions/42192420/python-post-requests-executed-twice-on-flask-app)
    app.run(host='0.0.0.0', port=8080, debug=True,
            threaded=True, use_reloader=False)
