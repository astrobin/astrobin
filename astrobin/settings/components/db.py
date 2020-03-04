import os

if os.environ.get("USE_SQLITE", 'false') == 'true':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'astrobin_test_db',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'astrobin',
            'USER': 'astrobin',
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'astrobin'),
            'HOST': os.environ.get('POSTGRES_HOST', 'postgres'),
            'PORT': '5432',
            'CONN_MAX_AGE': 60,
        }
    }

    if os.environ.get('POSTGRES_READ_REPLICA_HOST'):
        DATABASES['reader'] = {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'astrobin',
            'USER': 'astrobin',
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'astrobin'),
            'HOST': os.environ.get('POSTGRES_READ_REPLICA_HOST', 'postgres'),
            'PORT': '5432',
            'CONN_MAX_AGE': 60,
        }

        DATABASE_ROUTERS = ['astrobin.db.CustomRouter']

