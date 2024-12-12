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
import pathlib


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

    def start(self, flows_description: dict, experiment_dir: str = "./logs"):
        self.net.start()
        info("Starting network\n")
        self.start_servers(flows_description, experiment_dir)
        self.start_clients(flows_description)
        CLI(self.net)
        self.net.stop()

    def gen_mac_address(self, id: int):
        return f"00:00:00:00:00:{id:02x}"

    def start_servers(self, flows_description: dict, experiment_dir: str = "./logs"):
        for _, conn_info in flows_description.items():
            dst_host = self.hosts[conn_info["dst"]]
            dst = conn_info["dst"]
            src = conn_info["src"]
            report_period = conn_info["report_period"]
            ports = ""
            for flow_id, info in conn_info["flows"].items():
                ports = f"{ports}{info['port']}"
                if flow_id != list(conn_info["flows"].keys())[-1]:
                    ports = f"{ports},"

            # Create folder and log file
            pathlib.Path(experiment_dir).mkdir(parents=True, exist_ok=True)

            dst_host.cmd(
                f"(mgen port {ports} analytics window {report_period} output {experiment_dir}/c_{src}-s_{dst}.log) &"
            )

    def start_clients(self, flows_description: dict):
        for _, conn_info in flows_description.items():
            src = conn_info["src"]
            host_src = self.hosts[conn_info["src"]]
            dst = conn_info["dst"]
            events = ""
            disable_flows = ""
            for flow_id, info in conn_info["flows"].items():
                protocol = info["protocol"]
                port = info["port"]
                duration = info["duration"]
                traffic_pattern = info["traffic_pattern"]
                traffic_parameter = info["traffic_parameter"]
                events = f"{events} event '0.0 ON {flow_id} {protocol} SRC {port} DST 10.0.0.{dst+1}/{port} {traffic_pattern} {traffic_parameter}'"
                disable_flows = f"{disable_flows} event '{duration} OFF {flow_id}'"

            host_src.cmd(f"mgen {events} {disable_flows} report &")


def main():
    setLogLevel("info")
    topo_params = {
        "bandwidth": "capacity",
        "delay": "delay",
        "loss": "loss",
    }
    flows_description = {
        "conn_0": {
            "src": 0,
            "dst": 2,
            "report_period": 1,
            "flows": {
                "0": {
                    "duration": 10,
                    "traffic_pattern": "PERIODIC",
                    "traffic_parameter": "[1000 1024]",
                    "port": 5001,
                    "protocol": "UDP",
                },
                "1": {
                    "duration": 10,
                    "traffic_pattern": "PERIODIC",
                    "traffic_parameter": "[500 1024]",
                    "port": 5002,
                    "protocol": "UDP",
                },
            },
        },
        "conn_1": {
            "src": 1,
            "dst": 2,
            "report_period": 1,
            "flows": {
                "0": {
                    "duration": 10,
                    "traffic_pattern": "PERIODIC",
                    "traffic_parameter": "[100 1024]",
                    "port": 5003,
                    "protocol": "UDP",
                },
            },
        },
    }
    network = Network(topo_file="simple.txt", topo_params=topo_params)
    network.start(flows_description=flows_description)


if __name__ == "__main__":
    main()
