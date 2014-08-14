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

Start supervisord:

```bash
sudo /etc/init.d/supervisor start
```

Become the user 'astrobin':

```bash
sudo su - astrobin
```

Create a superuser:

```bash
./manage.py createsuperuser
```

Start AstroBin:

```bash
./manage.py runserver 0.0.0.0:8082
```

Visit http://127.0.0.1:8082/
