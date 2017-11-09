# AstroBin

AstroBin is an image hosting website for astrophotographers. The original production copy is run on https://www.astrobin.com/.

# Development

You can setup a development environment using [Vagrant](https://www.vagrantup.com/).

## Clone the code:

```bash
git clone https://github.com/astrobin/astrobin.git
cd astrobin
git submodule init
git submodule update
```

## Configure the system

Copy `env/example` to `env/dev` and set all the variables.

## Setup Vagrant

[Install Vagrant](https://www.vagrantup.com/docs/installation/index.html) and consult its [documentation](https://www.vagrantup.com/intro/getting-started/index.html)

Then create a Ubuntu 16.04 box:

```bash
vagrant init ubuntu/xenial64
vagrant up
```

## Login into the AstroBin's Vagrant box:

```bash
vagrant ssh
sudo su - astrobin
```

## Run it

```./scripts/run.sh```

And then visit http://127.0.0.1:8083/ from your host.


# Setting up a production server.

https://www.astrobin.com/ runs on the following components, and we recommend you use the same stack:
  - nginx
  - gunicorn
  - postgresql
  - elasticsearch
  - redis
  - memcached

It is recommended that you copy `env/dev` to `env/prod` and set some production specific variables there (like disabling `ASTROBIN_DEBUG`, etc). FYI, the `crontab` below references `env/prod`.
## nginx

```nginx
# Rate limit bots
map $http_user_agent $limit_bots {
    default '';
    ~*(bing|yandex|msnbot) $binary_remote_addr;
}
limit_req_zone $limit_bots zone=bots:10m rate=1r/m;

# The main server (port 8082 served by gunicorn)
upstream app_server {
    server 127.0.0.1:8082 fail_timeout=0;
}

# Redirect URLs without www
server {
        listen   80;
        server_name astrobin.com;
        rewrite ^/(.*) http://www.astrobin.com/$1 permanent;
}

server {
    listen 80 default;
    listen 443 default ssl;

    # No upload limits
    client_max_body_size 4G;

    server_name www.astrobin.com;
    error_page 502 503 /media/static/html/502.html;

    # Logs
    access_log /var/log/nginx/astrobin.com-access.log;
    error_log /var/log/nginx/astrobin.com-error.log;

    # Certs
    ssl_certificate      /etc/ssl/localcerts/astrobin.com-ssl-bundle.crt;
    ssl_certificate_key  /etc/ssl/localcerts/www.astrobin.com.key;

    keepalive_timeout 5;
    proxy_read_timeout 1200;

    ## Compression
    # src: http://www.ruby-forum.com/topic/141251
    # src: http://wiki.brightbox.co.uk/docs:nginx

    gzip on;
    gzip_http_version 1.0;
    gzip_comp_level 2;
    gzip_proxied any;
    gzip_min_length  1100;
    gzip_buffers 16 8k;
    gzip_types text/plain text/css application/x-javascript text/xml application/xml application/xml+rss text/javascript;

    # Some version of IE 6 don't handle compression well on some mime-types, so just disable for them
    gzip_disable "MSIE [1-6].(?!.*SV1)";

    # Set a vary header so downstream proxies don't send cached gzipped content to IE6
    gzip_vary on;
    ## /Compression

    # Serve static files
    location /media/  {
        root /var/www;
        expires 30d;
    }

    # Faw RawData
    location /tmpzips/  {
        root /var/www;
        expires 3d;
    }

    # Favicon
    location /favicon.ico {
        root /media/static;
        expires max;
    }

    # Main server location
    location / {
        limit_req zone=bots burst=5 nodelay;
        if ($request_uri ~* "^/robots.txt") {
            rewrite ^/robots.txt /media/static/robots.txt permanent;
        }

        proxy_no_cache $http_pragma $http_authorization;
        proxy_cache_bypass $http_pragma $http_authorization;

        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $http_host;
        proxy_set_header HTTP_AUTHORIZATION $http_authorization;
        proxy_redirect off;
        if (!-f $request_filename) {
            proxy_pass http://app_server;
            break;
        }
    }
}
```

## Gunicorn

The actual app is served by gunicorn, which is controlled by supervisord. Your `/etc/supervisord/conf.d/gunicorn.conf` should look like this:

```supervisord
[program:gunicorn]
command = /venv/astrobin/dev/bin/python manage.py run_gunicorn 0.0.0.0:8082 -w 9 -p gunicorn.pid
directory = /var/www/astrobin/
user = astrobin
numprocs = 1
stdout_logfile = /var/log/gunicorn/default.log
stderr_logfile = /var/log/gunicorn/default.err
autostart = true
autorestart = true
startsecs = 10
environment =
	DJANGO_SETTINGS_MODULE='settings',
	... insert and configure all variables from env/example here ...
```

## Celery

AstroBin needs [celery](http://celery.readthedocs.io/en/latest/) to function properly. Celery is used for real-time searchi ndex updates and for RawData tasks.

You should serve celery via supervisord, and your `/etc/supervisord/conf.d/celery.conf` should look like this:

```supervisord
[program:celeryd]
command = /venv/astrobin/dev/bin/python manage.py celeryd -Q default -c 2 -E --pidfile=celeryd.pid --logfile=celeryd.log
directory = /var/www/astrobin
user = astrobin
numprocs = 1
stdout_logfile = /var/log/celery/default.log
stderr_logfile = /var/log/celery/default.err
autostart = true
autorestart = true
startsecs = 10
environment =
	DJANGO_SETTINGS_MODULE='settings',
	... insert and configure all variables from env/example here ...
```

## Postgresql

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

You may want to configure `work_mem` to be your RAM in GB, times 16, divided by the number of CPUs in your server.


# Running regular tasks

AstroBin needs some tasks to be run regularly, so here's a `crontab` that you should use:

```crontab
MAILTO=admin@astrobin.com

ASTROBIN_ROOT=/var/www/astrobin
PYTHON=/venv/astrobin/dev/bin/python

TMPZIPS=/var/www/tmpzips
IMGCACH=/var/www/media/imagecache

# Sync the old IOTD tables to the new ones, for API compatibility purposes.
00 00 * * * (. $ASTROBIN_ROOT/env/prod; cd $ASTROBIN_ROOT; $PYTHON ./manage.py image_of_the_day) 2>&1 >/dev/null

# Update the search index, which affects search, the Wall, the stats, and the AstroBin Index.
00 03 * * * (. $ASTROBIN_ROOT/env/prod; cd $ASTROBIN_ROOT; $PYTHON ./manage.py update_index --remove) 2>&1 >/dev/null

# Try to remove Gear duplicates
10 00 * * 0 (. $ASTROBIN_ROOT/env/prod; cd $ASTROBIN_ROOT; $PYTHON ./manage.py merge_gear) 2>&1 >/dev/null

# Clean up "hits" to manage database disk space. We only care about the count after all.
20 00 * * * (. $ASTROBIN_ROOT/env/prod; cd $ASTROBIN_ROOT; $PYTHON ./manage.py hitcount_cleanup) 2>&1 >/dev/null

# CAREFUL! This will delete the users that own images marked as spam. Not enabled by default in this crontab.
#30 00 * * * (. $ASTROBIN_ROOT/env/prod; cd $ASTROBIN_ROOT; $PYTHON ./manage.py delete_spammers) 2>&1 >/dev/null

# Delete expired subscriptions so people may resubscribe eventually.
00 05 * * * (. $ASTROBIN_ROOT/env/prod; cd $ASTROBIN_ROOT; $PYTHON ./manage.py fix_expired_subscriptions) 2>&1 >/dev/null

# Again to manage database dist space, old notifications should be deleted periodically.
00 23 * * * (. $ASTROBIN_ROOT/env/prod; $PYTHON $ASTROBIN_ROOT/manage.py purge_old_notifications) 2>&1 >/dev/null

# Updates some global website stats, only available to superusers.
30 00 * * * (. $ASTROBIN_ROOT/env/prod; $PYTHON $ASTROBIN_ROOT/manage.py global_stats) 2>&1 >/dev/null

# Clean up caches
00 */1 * * * ($ASTROBIN_ROOT/scripts/contain_directory_size.sh $IMGCACH 5000000) 2>&1 >/dev/null
10 01 * * * (find $TMPZIPS -type f -name "*.zip" -mtime +2 -exec rm -f {} \; 2>&1 >/dev/null)

# Clean up temporary files
00 05 * * * (rm -rf /tmp/tmp.fits.*; rm -rf /tmp/tmp.ppm.*; rm -rf /tmp/tmp*.upload) 2>&1 >/dev/null
```

# Contributing

AstroBin accept contributions. Please fork the project and submit pull requests!
If you need support, please use the [astrobin-dev Google Group](https://groups.google.com/forum/#!forum/astrobin-dev).
