from os import listdir
from os.path import isfile, join
import re
import matplotlib.pyplot as plt

logs_dir = "./logs/example"

log_files = [file for file in listdir(logs_dir) if isfile(join(logs_dir, file))]
flows = {
    "goodput": {},
    "loss": {},
    "latency_ave": {},
}
for file in log_files:
    with open(f"{logs_dir}/{file}") as f:
        lines = f.readlines()
        for line in lines:
            if "REPORT" in line:
                goodput_re = re.search("rate>(.*) kbps", line)
                src_re = re.search("src>(.*) dst>", line)
                latency_re = re.search("latency ave>(.*) min>", line)
                loss_re = re.search("loss>(.*) latency ave", line)
                assert goodput_re is not None, "Goodput not found"
                assert src_re is not None, "Source not found"
                assert latency_re is not None, "Latency not found"
                assert loss_re is not None, "Loss not found"
                goodput = float(goodput_re.group(1))
                src = src_re.group(1)
                latency = float(latency_re.group(1))
                loss = float(loss_re.group(1))

                if src not in flows["goodput"]:
                    flows["goodput"][src] = []
                    flows["loss"][src] = []
                    flows["latency_ave"][src] = []
                flows["goodput"][src].append(goodput)
                flows["loss"][src].append(loss)
                flows["latency_ave"][src].append(latency)

plt.figure()
plt.title("Goodput")
for src, goodputs in flows["goodput"].items():
    plt.plot(goodputs, label=src)
plt.xlabel("Time(s)")
plt.ylabel("Goodput (kbps)")
plt.legend()
plt.grid()
plt.show()
