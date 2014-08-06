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

Run a dummy mail servers (for both debug and non-debug modes):

```bash
sudo python -m smtpd -n -c DebuggingServer localhost:25 &
python -m smtpd -n -c DebuggingServer localhost:1025 &
```


Become the user 'astrobin':

```bash
sudo -u astrobin /bin/bash
```

Init the environment:

```bash
. /var/www/astrobin/env/dev
. /venv/astrobin/dev/bin/activate
```

Create a superuser:

```bash
/var/www/astrobin/manage.py createsuperuser
```

Start AstroBin:

```bash
/var/www/astrobin/manage.py runserver 0.0.0.0:8082
```

Visit http://127.0.0.1:8082/
