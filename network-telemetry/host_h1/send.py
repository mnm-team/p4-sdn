#!/usr/bin/env python3
import sys
import time

from probe_hdrs import *


def main():

    # (h1, s1, s4, s2, s4, s5, s3,s1,h1)
    probe_pkt = Ether(dst='ff:ff:ff:ff:ff:ff', src=get_if_hwaddr('eth1')) / \
                Probe(hop_cnt=0) / \
                ProbeFwd(egress_spec=4) / \
                ProbeFwd(egress_spec=2) / \
                ProbeFwd(egress_spec=4) / \
                ProbeFwd(egress_spec=4) / \
                ProbeFwd(egress_spec=1) / \
                ProbeFwd(egress_spec=2) / \
                ProbeFwd(egress_spec=1)

    # (h1, s1, s3, s5, s4, s2, s4,s1,h1)
    #probe_pkt = Ether(dst='ff:ff:ff:ff:ff:ff', src=get_if_hwaddr('eth1')) / \
    #            Probe(hop_cnt=0) / \
    #            ProbeFwd(egress_spec=3) / \
    #            ProbeFwd(egress_spec=5) / \
    #            ProbeFwd(egress_spec=2) / \
    #            ProbeFwd(egress_spec=2) / \
    #            ProbeFwd(egress_spec=4) / \
    #            ProbeFwd(egress_spec=1) / \
    #            ProbeFwd(egress_spec=1)

    while True:
        try:
            sendp(probe_pkt, iface='eth1')
            time.sleep(1)
        except KeyboardInterrupt:
            sys.exit()

if __name__ == '__main__':
    main()
