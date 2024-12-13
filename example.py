from network_scenario import Network
from mininet.log import setLogLevel
import numpy as np


def create_flows_description(number_nodes: int) -> dict:
    num_conns = 2
    min_num_flows = 1
    max_num_flows = 3
    flows_description = {}
    rng = np.random.default_rng(seed=10)
    nodes = rng.choice(number_nodes, num_conns * 2, replace=False)
    srcs = nodes[:num_conns]  # First three chosen nodes are mgen clients
    dsts = nodes[num_conns:]  # Last three chosen nodes are mgen servers

    port_idx = 5001
    for conn_idx in range(num_conns):
        src = srcs[conn_idx]
        dst = dsts[conn_idx]
        flows_description[f"conn_{conn_idx}"] = {
            "src": int(src),
            "dst": int(dst),
            "report_period": 1,
            "flows": {},
        }
        num_flows = rng.integers(min_num_flows, max_num_flows + 1)
        for flow in range(num_flows):
            random_pattern_choice = np.random.choice(["PERIODIC", "POISSON", "BURST"])
            # Check Mgen traffic pattern documentation for more information
            if random_pattern_choice == "PERIODIC":
                min_packets_per_second = 100
                max_packets_per_second = 1000
                flows_description[f"conn_{conn_idx}"]["flows"][f"{flow}"] = {
                    "duration": 30,
                    "traffic_pattern": "PERIODIC",
                    "traffic_parameter": f"[{rng.integers(min_packets_per_second, max_packets_per_second)} 1024]",
                    "port": port_idx,
                    "protocol": "UDP",
                }
            elif random_pattern_choice == "POISSON":
                min_packets_per_second = 100
                max_packets_per_second = 1000
                flows_description[f"conn_{conn_idx}"]["flows"][f"{flow}"] = {
                    "duration": 30,
                    "traffic_pattern": "POISSON",
                    "traffic_parameter": f"[{rng.integers(min_packets_per_second, max_packets_per_second)} 1024]",
                    "port": port_idx,
                    "protocol": "UDP",
                }
            elif random_pattern_choice == "BURST":
                min_packets_per_second = 100
                max_packets_per_second = 1000
                flows_description[f"conn_{conn_idx}"]["flows"][f"{flow}"] = {
                    "duration": 30,
                    "traffic_pattern": "BURST",
                    "traffic_parameter": f"[REGULAR 5.0 PERIODIC [{rng.integers(min_packets_per_second, max_packets_per_second)} 1024] EXP 5.0]",
                    "port": port_idx,
                    "protocol": "UDP",
                }
            else:
                raise ValueError("Invalid traffic pattern")
            port_idx += 1

    return flows_description


def main():
    setLogLevel("info")
    topo_params = {
        "bandwidth": "capacity",
        "delay": "delay",
        "loss": "loss",
    }
    time_wait_topology = 20  # seconds (if it is too small, the topology may not be available in the ONOS yet)
    time_wait_traffics = 10  # seconds (if it is too small, the flows may not be available in the ONOS yet)
    exp_duration = 30  # seconds (Will close the mininet topology after this time + time_wait_topology + time_wait_traffics)
    network = Network(topo_file="simple.txt", topo_params=topo_params)
    flows_description = create_flows_description(len(network.net.hosts))
    print("Flows description:\n", flows_description)
    network.start(
        time_wait_topology=time_wait_topology,
        time_wait_traffics=time_wait_traffics,
        exp_duration=exp_duration,
        flows_description=flows_description,
        experiment_dir="./logs/example",
    )


if __name__ == "__main__":
    main()
