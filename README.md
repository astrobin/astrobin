[![Build Status](https://travis-ci.org/astrobin/astrobin.svg?branch=master)](https://travis-ci.org/astrobin/astrobin)
[![codecov](https://codecov.io/gh/astrobin/astrobin/branch/master/graph/badge.svg)](https://codecov.io/gh/astrobin/astrobin)
[![Updates](https://pyup.io/repos/github/astrobin/astrobin/shield.svg)](https://pyup.io/repos/github/astrobin/astrobin/)

![AstroBin](astrobin/static/images/astrobin-logo.png)

AstroBin is an image hosting website for astrophotographers. The original
production copy is run on https://www.astrobin.com/.

# Development

You can setup a development environment using Docker.

## Clone the code:

```bash
git clone https://github.com/astrobin/astrobin.git
cd astrobin
git submodule init
git submodule update
```

## Configure the system

You will need to edit two files, `docker/astrobin.env` and `docker/secret.env`.
To avoid committing your passwords to the repository, remember to instruct git
to ignore changes to those files:

```bash
git update-index --assume-unchanged docker/astrobin.env
git update-index --assume-unchanged docker/secrets.env
```

## Setup Docker

[Install Docker](https://www.docker.com/), then create and run the containers:

```bash
docker-compose -f docker/docker-compose.yml up -d
```

The first time you create a container for AstroBin, you will need to run the following:

```bash
docker-compose -f docker/docker-compose.yml run --no-deps --rm astrobin ./scripts/init.sh
```

To make all the static files available to the app, run:

```bash
docker-compose -f docker/docker-compose.yml run --no-deps --rm astrobin python manage.py collectstatic --noinput
```

This might take a while, especially if run against AWS.


AstroBin is running! Visit http://127.0.0.1/ from your host.

*PLEASE NOTE*: the nginx configuration in `docker/nginx.conf` is meant for a
production environment. Feel free to tune if you change things.

## Debugging

For debugging purposes, it is recommended that you launch a simple development
server on port 8084, and then access it directly bypassing nginx.

```bash
docker exec -it astrobin python manage.py runserver 0.0.0.0:8084
```

# Postgresql

The following indexes are recommended for your Postgresql server:

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
