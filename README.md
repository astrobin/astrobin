[![Build Status](https://travis-ci.org/astrobin/astrobin.svg?branch=master)](https://travis-ci.org/astrobin/astrobin)
[![codecov](https://codecov.io/gh/astrobin/astrobin/branch/master/graph/badge.svg)](https://codecov.io/gh/astrobin/astrobin)
[![Updates](https://pyup.io/repos/github/astrobin/astrobin/shield.svg)](https://pyup.io/repos/github/astrobin/astrobin/)

![AstroBin](astrobin/static/images/astrobin-logo.png)

AstroBin is an image hosting website for astrophotographers. The original
production copy is run on https://www.astrobin.com/.

# Architecture overview

![Architecture overview](https://raw.githubusercontent.com/astrobin/astrobin/master/graphics/astrobin-architecture.png)

AstroBin is composed by several components. The following paragraphs shortly
describes what they are, what they do, and what their relationships are.

### nginx
The proxy server that sits in front of the app and forwards the requests.

### AstroBin app
The actual main app.

### rabbitmq
The asynchronous message queue used to orchestrate background tasks.

### celery beat
The periodic task scheduler. Think of it as a cron daemon.

### celery worker
The background task worker. Background tasks include:
  - sending emails
  - updating the search index
  - doing some performance intensive tasks
  - periodically cleaning up caches

### db
The postgres database that holds all the data.

### cache
The memcache daemon that store transient data for performance reasons.

### search
The Elasticsearch engine that handles the search index. It's accessed by
the AstroBin app directly for queries, and by the celery worker to update
the index.

### wdb
A debug server that can be used in debug mode to interactively debug the app.

### flower
A monitor that sits on top of rabbitmq and monitors the celery tasks.


# Development

You can setup a development environment using Docker.

## Step 1: Clone the code:

```bash
git clone https://github.com/astrobin/astrobin.git
cd astrobin
git submodule init
git submodule update
```

## Step 2: Configure the system

The `docker/astrobin.env` file contains configuration information for
AWS, PayPal, Google Analytics, e-mail service, and others.  The default
settings are sufficient to bring up a full Astrobin site on your
workstation, so you should not need to make any changes here at first.

But to avoid committing your passwords to the repository, remember
to instruct git to ignore changes to this file:

```bash
git update-index --assume-unchanged docker/astrobin.env
```

## Step 3: Setup Docker

[Install Docker](https://store.docker.com/search?type=edition&offering=community),
and make sure you have the latest stable version of [docker-compose](https://github.com/docker/compose/releases)
installed.

## Step 4: Bring up the stack

The `docker-compose.yml` file contains all the instructions needed to bring up the
stack, including how to build the `astrobin`, `nginx`, `celery`, and `beat` containers.

```bash
docker-compose -f docker/docker-compose.yml up -d
```

## Step 5: First-time setup

The first time you launch AstroBin (and only the first time), you will find that
it's not quite working yet.  For example, the `beat` container refuses to start,
and accessing http://127.0.0.1/ brings up the site, but without any CSS or javascript.

These need to be initialized by running the following commands.

The `init.sh` script does some initial django initialization, like creating groups, a superuser,
and the "site" configuration.

```bash
docker-compose -f docker/docker-compose.yml run --no-deps --rm astrobin ./scripts/init.sh
```

Then, to make all the static files (CSS, javascript, images, etc.) available to the app, run:

```bash
docker-compose -f docker/docker-compose.yml run --no-deps --rm astrobin python manage.py collectstatic --noinput
```

You'll need to manually restart the `beat` container after this; everything else should gracefully recover.

```bash
docker-compose -f docker/docker-compose.yml restart beat
```

## Step 6: Ensure services are running

```bash
docker-compose -f docker/docker-compose.yml ps
```

This shows you the containers running.  Check the `State` column and make sure
everything is `Up`. If you see `Restarting` or `Exit` that means the container didn't
start up properly on its own, and you may need to do some troubleshooting
in that container.

## Step 7: Login!

AstroBin is running! Visit http://127.0.0.1/ from your host. You can login with
the following credentials:

    astrobin_dev:astrobin_dev

## Step 8: Debugging server

For debugging purposes, it is recommended that you launch a simple development
server on port 8084, and then access it directly bypassing nginx.

```bash
docker exec -it astrobin python manage.py runserver 0.0.0.0:8084
```

## Resetting to a "from scratch" build

If something goes terribly wrong and you need to start over, or if you just want to validate that
your code works properly with a "clean" build of the site, you will need to reset things.

Most of the "state" is stored in the `docker_postgres-data` volume, which contains the PostgreSQL
database.  So a "lightweight" reset would be to do the following:

```bash
# bring down the stack
docker-compose -f docker/docker-compose.yml down

# delete the postgresql volume
docker volume rm docker_postgres-data

# bring the stack back up
docker-compose -f docker/docker-compose.yml up -d

# re-initialize django
docker-compose -f docker/docker-compose.yml run --no-deps --rm astrobin ./scripts/init.sh
```

But if you *really* want to start from scratch, for example to do a final thorough build and test
of your new code, then you can do a "heavyweight" reset:

```bash
./scripts/docker-reset.sh
```

This script will reset your Astrobin docker environment back to zero, so you can start over
at "step 1" of the build instructions above.

# Postgresql

The following indexes are recommended for your Postgresql server (feel free to
ignore this section for small or development installations):

```sql
create index on astrobin_image using btree (uploaded, id);
create index on actstream_action using btree (timestamp);
create index on toggleproperties_toggleproperty using btree(property_type, content_type_id, object_id);
create index on toggleproperties_toggleproperty using btree(property_type, content_type_id, created_on);
create index object_id_integer_cast on toggleproperties_toggleproperty (cast(toggleproperties_toggleproperty.object_id as int))
create index persistent_messages_message_user_id_read_idx on persistent_messages_message (user_id, read);
create index persistent_messages_message_created_idx on persistent_messages_message (created);
create index on hitcount_hit_count using btree(object_pk, content_type_id);
create index on nested_comments_nestedcomment using btree(deleted, object_id);
 ```

You may want to configure `work_mem` to be your RAM in GB, times 16, divided by
the number of CPUs in your server.

# Note on building the nginx container

```bash
export ENV=prod; docker build -t astrobin/nginx-${ENV} --build-arg ENV=${ENV} -f docker/nginx.dockerfile . && docker push astrobin/nginx-${ENV}
```

# Contributing

AstroBin accepts contributions. Please fork the project and submit pull
requests!
If you need support, please use the [astrobin-dev Google
Group](https://groups.google.com/forum/#!forum/astrobin-dev).
