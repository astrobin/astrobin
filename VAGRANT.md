# Vagrant

AstroBin is installed using Vagrant: http://www.vagrantup.com/

Vagrant provides easy to configure, reproducible, and portable work
environments built on top of industry-standard technology and controlled by a
single consistent workflow to help maximize the productivity and flexibility of
you and your team.

Consult Vagrant's documentation at:
http://docs.vagrantup.com/v2/getting-started/index.html


# Setting up an AstroBin box


First, install Vagrant using the means provided by your distribution. Consult the following:

http://docs.vagrantup.com/v2/installation/index.html

Then create a trusty64 box:

```bash
vagrant box add astrobin https://cloud-images.ubuntu.com/xenial/current/xenial-server-cloudimg-amd64-vagrant.box
```

Go to the directory that holds the AstroBin code and start the Vagrant box:

```bash
cd ~/code/astrobin
vagrant up
```

