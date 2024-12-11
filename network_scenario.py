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
            # controller=RemoteController, switch=OVSKernelSwitch, link=TCLink
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
            bw = edge[2].get(topo_params["bandwidth"], link_default_values["bandwidth"])
            delay = edge[2].get(topo_params["delay"], link_default_values["delay"])
            loss = edge[2].get(topo_params["loss"], link_default_values["loss"])
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
        # self.hosts[0].cmd("mgen input client.mgn &")
        # self.hosts[1].cmd("mgen input server.mgn &")
        CLI(self.net)
        self.net.stop()

    def gen_mac_address(self, id):
        return f"00:00:00:00:00:{id:02x}"

    def start_servers(self, flows_description):
        for flow, info in flows_description.items():
            src = self.hosts[info["src"]]
            dst = self.hosts[info["dst"]]
            protocol = info["protocol"]
            port = info["port"]
            duration = info["duration"]
            traffic_pattern = info["traffic_pattern"]
            windows = info["report_period"]

            dst.cmd(
                f"h{dst} mgen port {port} report analytics window {windows} output logs/host_{dst}.log"
            )


def main():
    setLogLevel("info")
    topo_params = {
        "bandwidth": "capacity",
        "delay": "delay",
        "loss": "loss",
    }
    flows_description = {
        "flow1": {
            "src": 0,
            "dst": 2,
            "protocol": "TCP",
            "port": 5001,
            "duration": 10,
            "traffic_pattern": "periodic",  # Can be periodic periodic, poisson, burst
            "report_period": 1,  # Seconds
        },
        "flow2": {
            "src": 0,
            "dst": 2,
            "protocol": "UDP",
            "port": 5002,
            "duration": 10,
            "traffic_pattern": "poisson",  # Can be periodic periodic, poisson, burst
            "report_period": 1,  # Seconds
        },
    }
    network = Network("simple.txt", topo_params)
    network.start()


if __name__ == "__main__":
    main()

# h2 mgen port 5001,5002 report analytics window 1 output logs/server.log
# h2 {mgen port 5001,5002 report analytics window 1 2>&1 | grep 'REPORT' > logs/server.log;} &
# h0 mgen report analytics window 1 event "0.0 ON 1 UDP SRC 5001 DST 10.0.0.3/5001 PERIODIC [1000 1024]" event "10.0 OFF 1"
