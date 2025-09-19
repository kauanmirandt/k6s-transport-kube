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
from time import sleep
from typing import Tuple
import requests
import json


class Network:
    def __init__(
        self,
        topo_file: str,
        topo_params: Optional[dict] = None,
        onos_addr: str = "127.0.0.1",
        onos_port: int = 31653,
        onos_api_port: int = 30181,
        onos_user: str = "onos",
        onos_pass: str = "rocks",
    ):
        self.net_topology = nx.read_gml(topo_file)
        self.net = Mininet(
            controller=RemoteController, switch=OVSKernelSwitch, link=TCLink
        )
        
        self.onos_api_adress = f"http://{onos_addr}:{onos_api_port}/onos/v1"
        self.onos_user = onos_user
        self.onos_pass = onos_pass
        self.net.addController(
            name="c0",
            controller=RemoteController,
            ip=onos_addr,
            protocol="tcp",
            port=onos_port,
        )
        
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
            id = int(node) + 1
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
            self.net.addLink(self.hosts[int(id) - 1], self.switches[int(id) - 1])

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

    def start(
        self,
        time_wait_topology: int,
        time_wait_traffics: int,
        exp_duration: int,
        flows_description: dict,
        experiment_dir: str = "./logs",
    ):
        self.net.start()
        info("Mininet topology started\n")
        sleep(time_wait_topology)
        self.start_servers(flows_description, experiment_dir)
        self.start_clients(flows_description)
        info("Traffic generator started\n")
        sleep(time_wait_traffics)
        self.get_onos_paths(flows_description, experiment_dir)
        sleep(exp_duration)
        info(f"Experiment finished. You can find log information in {experiment_dir}\n")
        # self.net.stop()
        # CLI(self.net)

    def gen_mac_address(self, id: int):
        return f"00:00:00:00:00:{id:02x}"

    def get_device_id(self, id: int):
        return f"of:{(id+1):016d}"

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
                f"bash -c '(mgen port {ports} analytics window {report_period} | grep REPORT > {experiment_dir}/c_{src}-s_{dst}.log)'&"
            )

    def start_clients(self, flows_description: dict):
        for _, conn_info in flows_description.items():
            host_src = self.hosts[conn_info["src"]]
            dst = conn_info["dst"] + 1
            events = ""
            disable_flows = ""
            for flow_id, info in conn_info["flows"].items():
                protocol = info["protocol"]
                port = info["port"]
                duration = info["duration"]
                traffic_pattern = info["traffic_pattern"]
                traffic_parameter = info["traffic_parameter"]
                events = f"{events} event '0.0 ON {flow_id} {protocol} SRC {port} DST 10.0.0.{dst}/{port} {traffic_pattern} {traffic_parameter}'"
                disable_flows = f"{disable_flows} event '{duration} OFF {flow_id}'"

            host_src.cmd(f"mgen {events} {disable_flows} report &")

    def get_onos_paths(self, flows_description: dict, experiment_dir: str = "./logs"):
        flows, links = self.get_onos_flows_links()
        conn_paths = {}
        for conn_id, conn_info in flows_description.items():
            src_dev_id = self.get_device_id(conn_info["src"])
            dst_dev_id = self.get_device_id(conn_info["dst"])
            src_port = "1"  # default host port det by ONOS
            conn_paths[conn_id] = [src_dev_id]

            while conn_paths[conn_id][-1] != dst_dev_id:
                dst_port = None
                curr_conn_path = conn_paths[conn_id].copy()
                for flow in flows:  # Find flow rule that matches the src port
                    if flow["deviceId"] == src_dev_id:
                        for criteria in flow["selector"]["criteria"]:
                            if criteria["type"] == "IN_PORT":
                                if str(criteria["port"]) == src_port:
                                    dst_port = flow["treatment"]["instructions"][0][
                                        "port"
                                    ]
                    if dst_port is not None:
                        break
                for link in links:  # Find the link to the next device
                    if (
                        link["src"]["device"] == src_dev_id
                        and link["src"]["port"] == dst_port
                    ):
                        src_port = link["dst"]["port"]
                        src_dev_id = link["dst"]["device"]
                        conn_paths[conn_id].append(src_dev_id)
                        break
                if conn_paths[conn_id] == curr_conn_path:
                    raise Exception("No path found")

        # Writing paths to external file
        with open(f"{experiment_dir}/conn_paths.json", "w") as f:
            json.dump(conn_paths, f)

    def get_onos_flows_links(self) -> Tuple[list, list]:
        flows = requests.get(
            self.onos_api_adress + "/flows", auth=(self.onos_user, self.onos_pass)
        )
        links = requests.get(
            self.onos_api_adress + "/links", auth=(self.onos_user, self.onos_pass)
        )
        if flows.status_code == 200 and links.status_code == 200:
            flows = flows.json()
            links = links.json()
        else:
            raise Exception("Failed to get flows and links from SDN controller")

        return flows["flows"], links["links"]


def main():
    setLogLevel("info")
    topo_params = {
        "bandwidth": "capacity",
        "delay": "delay",
        "loss": "loss",
    }
    time_wait_topology = 20  # seconds (if it is too small, the topology may not be available in the ONOS yet)
    time_wait_traffics = 10  # seconds (if it is too small, the flows may not be available in the ONOS yet)
    exp_duration = 300  # seconds (Will close the mininet topology after this time + time_wait_topology + time_wait_traffics)
    flows_description = {
        "conn_0": {
            "src": 0,
            "dst": 2,
            "report_period": 1,
            "flows": {
                "0": {
                    "duration": 300,
                    "traffic_pattern": "PERIODIC",
                    "traffic_parameter": "[1000 1024]",
                    "port": 5001,
                    "protocol": "UDP",
                },
                "1": {
                    "duration": 300,
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
                    "duration": 300,
                    "traffic_pattern": "PERIODIC",
                    "traffic_parameter": "[100 1024]",
                    "port": 5003,
                    "protocol": "UDP",
                },
            },
        },
    }
    network = Network(topo_file="simple.txt", topo_params=topo_params)
    network.start(
        time_wait_topology=time_wait_topology,
        time_wait_traffics=time_wait_traffics,
        exp_duration=exp_duration,
        flows_description=flows_description,
    )


if __name__ == "__main__":
    main()
