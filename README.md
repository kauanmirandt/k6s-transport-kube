# mgen_mininet

Integrating MGEN traffic generator with Mininet through python dictionaries.

## Requirements
- [MGEN version 5.1.1](https://github.com/USNavalResearchLaboratory/mgen)
- [Mininet version 2.3.0](https://github.com/mininet/mininet)
- [Pipenv](https://github.com/pypa/pipenv)
- [Docker](https://docs.docker.com/engine/install/)
- [Docker compose](https://docs.docker.com/compose/install/)

## Creating python environment
Execute `pipenv install` for installing all python requirements in the virtual environment.

## Running the example script
First, run the ONOS controller containers using the command `docker compose up -d`. You can check ONOS GUI accessing [here](http://127.0.0.1:8181/onos/ui/login.html) and using the user `onos` and password `rocks`. Execute `pipenv run example.py` to start the example script. The Mininet topology should appear in the ONOS GUI and the generated logs should be saved at `logs/example` folder.

**Remember of running `sudo mn -c` to close previous experiments completely and avoid interference with new ones.**

**We assume there is only one host per switch.**

## Plotting results
There is a simple script `analyse_results.py` for reading the MGEN outputs and getting the network metrics from reports to plot in a figure. You can use `pipenv run analyse_results.py`.