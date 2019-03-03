import os

engine = os.environ.get('DB_ENGINE', 'django.db.backends.postgresql_psycopg2')
SITE_ROOT = os.path.dirname(os.path.join(os.path.realpath(__file__)))

DATABASES = {
    'default': {
        'ENGINE': engine,
        'NAME': os.path.join(SITE_ROOT, 'db.sqlite3') if 'sqlite' in engine else 'astrobin',
        'USER': 'astrobin',
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'astrobin'),
        'HOST': os.environ.get('POSTGRES_HOST', 'postgres'),
        'PORT': '5432',
        'CONN_MAX_AGE': 60,
    }
}
