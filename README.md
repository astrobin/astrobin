[![Build Status](https://travis-ci.org/astrobin/astrobin.svg?branch=master)](https://travis-ci.org/astrobin/astrobin)

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

# Setting up a production server.

AstroBin.com is deployed on [Hyper.sh](https://hyper.sh/), but given that it's a
set of Docker containers, you are of course free to deploy as you see fit.

To deploy on Hyper.sh, simply run:

```bash
# ENV could be www or beta
ENV=www hyper compose up -f hyper-compose.yml -d
```

# Running regular tasks

AstroBin needs some tasks to be run regularly, so here's a `crontab` that you
should use:

```crontab
MAILTO=admin@astrobin.com

ASTROBIN_ROOT=/code
PYTHON=python

TMPZIPS=/media/tmpzips
IMGCACH=/media/imagecache

# Sync the old IOTD tables to the new ones, for API compatibility purposes.
00 00 * * * (cd $ASTROBIN_ROOT; $PYTHON ./manage.py image_of_the_day) 2>&1 >/dev/null

# Update the search index, which affects search, the Wall, the stats, and the AstroBin Index.
00 03 * * * (cd $ASTROBIN_ROOT; $PYTHON ./manage.py update_index --remove --workers=2) 2>&1 >/dev/null

# Try to remove Gear duplicates
10 00 * * 0 (cd $ASTROBIN_ROOT; $PYTHON ./manage.py merge_gear) 2>&1 >/dev/null

# Clean up "hits" to manage database disk space. We only care about the count after all.
20 00 * * * (cd $ASTROBIN_ROOT; $PYTHON ./manage.py hitcount_cleanup) 2>&1 >/dev/null

# CAREFUL! This will delete the users that own images marked as spam. Not enabled by default in this crontab.
#30 00 * * * (cd $ASTROBIN_ROOT; $PYTHON ./manage.py delete_spammers) 2>&1 >/dev/null

# Delete expired subscriptions so people may resubscribe eventually.
00 05 * * * (cd $ASTROBIN_ROOT; $PYTHON ./manage.py fix_expired_subscriptions) 2>&1 >/dev/null

# Send reminders about premium subscriptions about to expire.
00 08 * * * (cd $ASTROBIN_ROOT; $PYTHON ./manage.py send_expiration_notifications) 2>&1 >/dev/null

# Again to manage database dist space, old notifications should be deleted periodically.
00 23 * * * (cd $ASTROBIN_ROOT; $PYTHON $ASTROBIN_ROOT/manage.py purge_old_notifications) 2>&1 >/dev/null

# Updates some global website stats, only available to superusers.
30 00 * * * (cd $ASTROBIN_ROOT; $PYTHON $ASTROBIN_ROOT/manage.py global_stats) 2>&1 >/dev/null

# Clean up caches
00 */1 * * * ($ASTROBIN_ROOT/scripts/contain_directory_size.sh $IMGCACH 5000000) 2>&1 >/dev/null
10 01 * * * (find $TMPZIPS -type f -name "*.zip" -mtime +2 -exec rm -f {} \; 2>&1 >/dev/null)

# Clean up temporary files
00 05 * * * (rm -rf /tmp/tmp.fits.*; rm -rf /tmp/tmp.ppm.*; rm -rf /tmp/tmp*.upload) 2>&1 >/dev/null
```

The following commands create the relevant cron jobs on Hyper.sh:

```bash
export HYPER_ACCESS=(your Hyper.sh access key)
export HYPER_SECRET=(your Hyper.sh access secret)

hyper cron create \
    --name iotd-sync \
    --container-name sync-iotd \
    --env-file=docker/astrobin.env \
    --env-file=docker/secrets.env  \
    --env-file=docker/postgres.env \
    --link memcached \
    --link postgres \
    --link rabbitmq \
    --link elasticsearch \
    --hour=4 --minute=0 \
    astrobin/astrobin python manage.py image_of_the_day

hyper cron create \
    --name merge-gear \
    --container-name merge-gear \
    --env-file=docker/astrobin.env \
    --env-file=docker/secrets.env  \
    --env-file=docker/postgres.env \
    --link memcached \
    --link postgres \
    --link rabbitmq \
    --link elasticsearch \
    --hour=4 --minute=5 \
    astrobin/astrobin python manage.py merge_gear

hyper cron create \
    --name fix-expired-subscriptions \
    --container-name fix-expired-subscriptions \
    --env-file=docker/astrobin.env \
    --env-file=docker/secrets.env  \
    --env-file=docker/postgres.env \
    --link memcached \
    --link postgres \
    --link rabbitmq \
    --link elasticsearch \
    --hour=4 --minute=10 \
    astrobin/astrobin python manage.py fix_expired_subscriptions

hyper cron create \
    --name hitcount-cleanup \
    --container-name hitcount-cleanup \
    --env-file=docker/astrobin.env \
    --env-file=docker/secrets.env  \
    --env-file=docker/postgres.env \
    --link memcached \
    --link postgres \
    --link rabbitmq \
    --link elasticsearch \
    --hour=4 --minute=15 \
    astrobin/astrobin python manage.py hitcount_cleanup

hyper cron create \
    --name purge-old-notifications \
    --container-name purge-old-notifications \
    --env-file=docker/astrobin.env \
    --env-file=docker/secrets.env  \
    --env-file=docker/postgres.env \
    --link memcached \
    --link postgres \
    --link rabbitmq \
    --link elasticsearch \
    --week=6 --hour=4 --minute=20 \
    astrobin/astrobin python manage.py purge_old_notifications

hyper cron create \
    --name global-stats \
    --container-name global-stats \
    --env-file=docker/astrobin.env \
    --env-file=docker/secrets.env  \
    --env-file=docker/postgres.env \
    --link memcached \
    --link postgres \
    --link rabbitmq \
    --link elasticsearch \
    --week=6 --hour=4 --minute=25 \
    astrobin/astrobin python manage.py global_stats

hyper cron create \
    --name contain-image-cache \
    --container-name contain-image-cache \
    --env-file=docker/astrobin.env \
    --env-file=docker/secrets.env  \
    --env-file=docker/postgres.env \
    -e HYPER_ACCESS=$HYPER_ACCESS \
    -e HYPER_SECRET=$HYPER_SECRET \
    --hour=4 --minute=30 \
    hyperhq/hypercli \
    hyper exec -it astrobin \
    scripts/contain_directory_size.sh /media/imagecaghe 5000000

hyper cron create \
    --name contain-tmp-zips \
    --container-name contain-tmp-zips \
    --env-file=docker/astrobin.env \
    --env-file=docker/secrets.env  \
    --env-file=docker/postgres.env \
    -e HYPER_ACCESS=$HYPER_ACCESS \
    -e HYPER_SECRET=$HYPER_SECRET \
    --hour=4 --minute=35 \
    hyperhq/hypercli \
    hyper exec -it astrobin \
    find /media/tmpzips -type f -name "*.zip" -mtime +2 -exec rm -f {} \;

hyper cron create \
    --name update-index \
    --container-name update-index \
    --env-file=docker/astrobin.env \
    --env-file=docker/secrets.env  \
    --env-file=docker/postgres.env \
    --link memcached \
    --link postgres \
    --link rabbitmq \
    --link elasticsearch \
    --hour=4 --minute=40 \
    astrobin/astrobin python manage.py update_index --remove --workers=2

hyper cron create \
    --name send-expiration-notifications \
    --container-name send-expiration-notifications \
    --env-file=docker/astrobin.env \
    --env-file=docker/secrets.env  \
    --env-file=docker/postgres.env \
    --link memcached \
    --link postgres \
    --link rabbitmq \
    --link elasticsearch \
    --hour=18 --minute=0 \
    astrobin/astrobin python manage.py send_expiration_notifications

hyper cron create \
    --name renew-ssl \
    --container-name renew-ssl \
    -e HYPER_ACCESS=$HYPER_ACCESS \
    -e HYPER_SECRET=$HYPER_SECRET \
    --week=1 --hour=8 --minute=0 \
    hyperhq/hypercli hyper exec nginx certbot renew
```

Note: here's a shortcut to remove all hyper cron jobs:

```bash
hyper cron rm `hyper cron ls | awk '{print $1}' | grep -v Name`
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
export ENV=www; docker build -t astrobin/nginx-${ENV} --build-arg ENV=${ENV} -f docker/nginx.dockerfile . && docker push astrobin/nginx-${ENV}
export ENV=beta; docker build -t astrobin/nginx-${ENV} --build-arg ENV=${ENV} -f docker/nginx.dockerfile . && docker push astrobin/nginx-${ENV}
```

# Notes on HTTPS

To generate a LetsEncrypt certificate within the Hyper container:
```
hyper run --rm -it --link astrobin -v certs:/etc/letsencrypt astrobin/nginx-www \
    rm -rf /etc/letsencrypt/live/www.astrobin.com && \
    certbot certonly --authenticator webroot \
    --agree-tos -m astrobin@astrobin.com -n \
    -d astrobin.com --webroot-path /etc/letsencrypt

# or

hyper run --rm -it --link astrobin -v certs:/etc/letsencrypt astrobin/nginx-beta \
    rm -rf /etc/letsencrypt/live/beta.astrobin.com && \
    certbot certonly --authenticator webroot \
    --agree-tos -m astrobin@astrobin.com -n \
    -d beta.astrobin.com --webroot-path /etc/letsencrypt


```

# Contributing

AstroBin accepts contributions. Please fork the project and submit pull
requests!
If you need support, please use the [astrobin-dev Google
Group](https://groups.google.com/forum/#!forum/astrobin-dev).
