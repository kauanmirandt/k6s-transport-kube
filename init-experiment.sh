PYTHON=$(pipenv --venv)"/bin/python3"
INFLUXDB_ORG="lasse"
INFLUXDB_BUCKET="devices_ports"

influx bucket delete --name $INFLUXDB_BUCKET --org $INFLUXDB_ORG
influx bucket create --name $INFLUXDB_BUCKET --org $INFLUXDB_ORG

sudo mn -c

sudo $PYTHON network_scenario.py