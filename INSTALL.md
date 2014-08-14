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
sudo supervisorctl update
```

Become the user 'astrobin':

```bash
sudo su - astrobin
```

Create a superuser:

```bash
./manage.py createsuperuser
```

At this point, AstroBin is already running via `gunicorn` on port 8082, so
you can visit http://127.0.0.1:8082/ from your host.
However, you may also want to run a debugging session on the command line,
like this:

```bash
./manage.py runserver 0.0.0.0:8083
```

And then visit http://127.0.0.1:8083/ from your host.
