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
vagrant box add astrobin https://vagrantcloud.com/ubuntu/boxes/trusty64/versions/14.04/providers/virtualbox.box
```

Go to the directory that holds the AstroBin code and start the valgrant box:

```bash
cd ~/code/astrobin
vagrant up
```

