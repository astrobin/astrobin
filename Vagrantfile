# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant::configure("2") do |config|
  config.vm.box = "astrobin"

  config.vm.provider "virtualbox" do |v|
    v.memory = 1024
    v.cpus = 2
  end

  config.vm.synced_folder ".", "/var/www/astrobin", mount_options:["uid=2000,gid=2000"]
  config.vm.network "forwarded_port", guest: 80, host: 8080
  config.vm.network "forwarded_port", guest: 8082, host: 8082

  config.vm.provision "shell" do |s|
    s.path = "./Vagrant/astrobin.sh"
    s.args = "#{ENV['VAGRANT_VERBOSE']}"
  end
end
