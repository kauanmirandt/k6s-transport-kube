Vagrant.configure("2") do |config|
  config.vm.provider :libvirt do |libvirt|
    libvirt.cpus = 12
    libvirt.memory = 10000 # Amount of RAM in MB
    libvirt.disk_driver :cache => 'none'
    libvirt.graphics_type = "none"
  end
  config.vm.box = "generic/ubuntu2204"
  config.vm.hostname = "mininet"
  config.vm.disk :disk, size: "20GB", primary: true
  config.vm.synced_folder './', "/home/vagrant/mgen_mininet"
  config.vm.network 'private_network', ip: '192.168.50.10'

  config.vm.provision "init", type: "shell", inline: <<-SHELL
    sudo apt update -y && sudo apt install -y software-properties-common mininet=2.2.2-5ubuntu1 python3-pip screen libpcap-dev
    sudo add-apt-repository ppa:deadsnakes/ppa -y && sudo apt update -y && sudo apt install python3.12 -y
    curl -sS https://bootstrap.pypa.io/get-pip.py | sudo python3.12
    sudo pip3.12 install --upgrade setuptools six requests
    sudo pip3.12 install mininet networkx schedule
    git clone https://github.com/USNavalResearchLaboratory/mgen.git && cd mgen && git submodule update --init && git checkout V5.1.1 && cd makefiles && make -f Makefile.linux
  SHELL
  # config.vm.provision "start", type: "shell", run: "always", inline: <<-SHELL
  #   sudo mn -c && sudo killall -q -w python3.12
  #   set -o allexport; source /home/vagrant/demo-erday/system.env; set +o allexport
  #   cd /home/vagrant/demo-erday/physical_twin
  #   bash -c 'screen -S run -dm sudo -E python3.12 main.py --num-flows 2 --bandwidths "1M,10M" --tos-values "0x10,0x20" --packet-size "125,125"'
  # SHELL
end
