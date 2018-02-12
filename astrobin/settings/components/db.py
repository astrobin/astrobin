import os

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

