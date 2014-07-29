# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant::configure("2") do |config|
  config.vm.box = "astrobin"

  config.vm.provider "virtualbox" do |v|
    v.memory = 1024
    v.cpus = 2
  end

  config.vm.synced_folder ".", "/var/www/astrobin", owner: "astrobin", group: "astrobin"
  config.vm.network "forwarded_port", guest: 80, host: 8080
  config.vm.network "forwarded_port", guest: 8082, host: 8082

  config.vm.provision "shell", path: "./Vagrant/init_system.sh"
  config.vm.provision "shell", path: "./Vagrant/apt.sh"
  config.vm.provision "shell", path: "./Vagrant/pip.sh", privileged: false
  config.vm.provision "shell", path: "./Vagrant/postgres.sh"
  config.vm.provision "shell", path: "./Vagrant/rabbitmq.sh"
  config.vm.provision "shell", path: "./Vagrant/supervisor.sh"
  config.vm.provision "shell", path: "./Vagrant/abc.sh"
  config.vm.provision "shell", path: "./Vagrant/init_astrobin.sh", privileged: false
  config.vm.provision "shell", path: "./Vagrant/init_db.sh", privileged: false
  config.vm.provision "shell", path: "./Vagrant/solr.sh"
end
