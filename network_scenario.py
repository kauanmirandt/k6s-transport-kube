#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.node import Host
from mininet.node import OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink
import networkx as nx
from typing import Optional


class Network:
    def __init__(self, topo_file: str, topo_params: Optional[dict] = None):
        self.net_topology = nx.read_gml(topo_file)
        self.net = Mininet(
            controller=RemoteController, switch=OVSKernelSwitch, link=TCLink
        )
        self.net.addController("c0")
        self.switches = []
        self.hosts = []
        if topo_params is None:
            topo_params = {
                "bandwidth": "bandwidth",
                "delay": "delay",
                "loss": "loss",
            }
        link_default_values = {
            "bandwidth": 100,
            "delay": "1ms",
            "loss": 0,
        }

        # Creating switches and hosts
        for node in self.net_topology.nodes:
            id = int(node)
            # Switch
            curr_switch = self.net.addSwitch(
                f"s{id}",
                cls=OVSKernelSwitch,
                protocols="OpenFlow10",
                mac_address=self.gen_mac_address(id),
            )
            self.switches.append(curr_switch)
            # Host
            curr_host = self.net.addHost(
                f"h{id}",
                cls=Host,
            )
            self.hosts.append(curr_host)
            # Creating links between switch and host
            self.net.addLink(self.hosts[int(id)], self.switches[int(id)])

        # Creating switch links
        for edge in self.net_topology.edges(data=True):
            src = int(edge[0])
            dst = int(edge[1])
            bw = edge.get(topo_params["bandwidth"], link_default_values["bandwidth"])
            delay = edge.get(topo_params["delay"], link_default_values["delay"])
            loss = edge.get(topo_params["loss"], link_default_values["loss"])
            self.net.addLink(
                self.switches[src],
                self.switches[dst],
                bw=bw,
                delay=delay,
                loss=loss,
            )

    def start(self):
        self.net.start()
        info("Starting network\n")
        CLI(self.net)
        self.net.stop()

    def gen_mac_address(self, id):
        return f"00:00:00:00:00:{id:02x}"


def main():
    setLogLevel("info")
    network = Network("topology.txt")
    network.start()


if __name__ == "__main__":
    main()
