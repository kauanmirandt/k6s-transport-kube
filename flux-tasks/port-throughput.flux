option task = {
  name: "device_ports_throughput_per_port",
  every: 5s,
  offset: 0s,
  retry: 2
}

from(bucket: "devices_ports")
  |> range(start: -20s)
  |> filter(fn: (r) =>
    r._measurement == "device_ports" and
    (r._field == "bytesReceived" or r._field == "bytesSent")
  )
  |> sort(columns: ["_time"])
  |> group(columns: ["device", "port", "_field"])
  |> derivative(unit: 1s, nonNegative: true)
  |> filter(fn: (r) => exists r._value)
  |> map(fn: (r) => ({
      _time: r._time,
      _measurement: "device_ports_throughput",
      _field: if r._field == "bytesReceived" then "rx_Mbps" else "tx_Mbps",
      _value: r._value * 8.0 / 1000000.0,
      device: r.device,
      port: r.port
  }))
  |> to(bucket: "devices_ports", org: "lasse")  
