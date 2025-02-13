import os

if os.environ.get("USE_SQLITE", 'false').strip() == 'true':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'astrobin_test_db',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB', 'astrobin').strip(),
            'USER': 'astrobin',
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'astrobin').strip(),
            'HOST': os.environ.get('POSTGRES_HOST', 'postgres').strip(),
            'PORT': '5432',
            'CONN_MAX_AGE': 60,
        }
    }

    if os.environ.get('POSTGRES_READ_REPLICA_HOST'):
        DATABASES['reader'] = {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB', 'astrobin').strip(),
            'USER': 'astrobin',
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'astrobin').strip(),
            'HOST': os.environ.get('POSTGRES_READ_REPLICA_HOST', 'postgres').strip(),
            'PORT': '5432',
            'CONN_MAX_AGE': 60,
        }
        REPLICA_DATABASES = ['reader']
        MULTIDB_PINNING_SECONDS = 1
        DATABASE_ROUTERS = ('multidb.PinningReplicaRouter',)

    if os.environ.get('POSTGRES_READ_REPLICA_SEGREGATED_HOST'):
        DATABASES['segregated_reader'] = {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB', 'astrobin').strip(),
            'USER': 'astrobin',
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'astrobin').strip(),
            'HOST': os.environ.get('POSTGRES_READ_REPLICA_SEGREGATED_HOST', 'postgres').strip(),
            'PORT': '5432',
            'CONN_MAX_AGE': 60,
        }
