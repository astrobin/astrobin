# Init the code

Checkout the submodules:

```bash
git submodule init
git submodule update
```

# Configure the system

Copy `env/example` to `env/dev` and set all the variables.
Set all the variables also in the `conf/supervisord/*` files.


# Install the Vagrant box

See VAGRANT.md.


# Run it

Enter the Vagrant box: `vagrant ssh`.
Init the environment:

```bash
. /var/www/astrobin/env/dev
. /venv/astrobin/dev/bin/activate
```

Start AstroBin: `/var/www/astrobin/scripts/run.sh`
Visit http://localhost:8082/
