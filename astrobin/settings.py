# Django settings for astrobin project.

from django.conf import global_settings

DEBUG = False
TEMPLATE_DEBUG = DEBUG
MAINTENANCE_MODE = False

ADMINS = (
    ('Salvatore Iovene', 'salvatore@iovene.com'),
)

MANAGERS = ADMINS
SERVER_EMAIL = 'astrobin@astrobin.com'
DEFAULT_FROM_EMAIL = 'AstroBin <astrobin@astrobin.com>'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'astrobin',     # Or path to database file if using sqlite3.
        'USER': 'astrobin',         # Not used with sqlite3.
        'PASSWORD': 'h3C_U77a', # Not used with sqlite3.
        'HOST': '',             # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',             # Set to empty string for default. Not used with sqlite3.
    }
}
DEFAULT_CHARSET = 'utf-8'

ASTROBIN_BASE_URL = 'http://astrobin.com'
ASTROBIN_SHORT_BASE_URL = 'http://astrob.in'

ASTROBIN_BASE_PATH = '/home/astrobin/Code/astrobin'
UPLOADS_DIRECTORY = ASTROBIN_BASE_PATH + '/uploads/'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'
LANGUAGE_COOKIE_NAME = 'astrobin_lang'

gettext = lambda s: s
LANGUAGES = (
    ('en', gettext('English')),
    ('it', gettext('Italian')),
)

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True
USE_L10N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ASTROBIN_BASE_PATH + '/static'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/static/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin-media/admin/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '4a*^ggw_5#w%tdf0q)=zozrw!avlts-h&&(--wy9x&p*c1l10g'

# Django storages
DEFAULT_FILE_STORAGE = 'astrobin.backends.s3boto.S3BotoStorage'
AWS_ACCESS_KEY_ID = 'AKIAJ46VGDGOKKHGGOAQ'
AWS_SECRET_ACCESS_KEY = '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'
AWS_STORAGE_BUCKET_NAME = 'astrobin_images'

from S3 import CallingFormat
AWS_CALLING_FORMAT = CallingFormat.SUBDOMAIN

# see http://developer.yahoo.com/performance/rules.html#expires
AWS_HEADERS = {
    'Expires': 'Thu, 15 Apr 2020 20:00:00 GMT',
    'Cache-Control': 'max-age=86400',
    'x-amz-acl': 'public-read',
    
    }
S3_URL = 's3.amazonaws.com'

RESIZED_IMAGE_SIZE = 720
THUMBNAIL_SIZE = 168 
SMALL_THUMBNAIL_SIZE = 84
ABPOD_SIZE = 350

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
#    'django.middleware.cache.UpdateCacheMiddleware', # KEEP AT THE BEGINNING
    'django.middleware.http.ConditionalGetMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.locale.LocaleMiddleware',
#   'django.middleware.csrf.CsrfViewMiddleware',
#   'django.middleware.csrf.CsrfResponseMiddleware',
#   'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
#   'astrobin.middlewares.ProfilerMiddleware',
#   'astrobin.middlewares.VaryOnLangCacheMiddleware',
    'privatebeta.middleware.PrivateBetaMiddleware',
    'maintenancemode.middleware.MaintenanceModeMiddleware',
#    'django.middleware.cache.FetchFromCacheMiddleware', # KEEP AT THE END
)

ROOT_URLCONF = 'astrobin.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    ASTROBIN_BASE_PATH + '/astrobin/templates',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
    'django.core.context_processors.auth',
    'notification.context_processors.notification',
    'astrobin.context_processors.privatebeta_enabled',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'astrobin',
    'django.contrib.admin',
    'registration',
    'djangoratings',
    'compressor',
    'haystack',
    'notification',
    'debug_toolbar',
    'persistent_messages',
    'djcelery',
    'gunicorn',
    'privatebeta',
    'south',
)

LOGIN_REDIRECT_URL = '/'
ACCOUNT_ACTIVATION_DAYS = 7
AUTH_PROFILE_MODULE = 'astrobin.UserProfile'

FLICKR_API_KEY = '1f44b18e230b8c9816a39d9b34c3318d'
FLICKR_SECRET  = 'd5fdb83e9aa995fc'

# Turn COMPRESS to True for deployment
COMPRESS = False
COMPRESS_URL = '/static/'
COMPILER_FORMATS = {
    '.less': {
        'binary_path':'lessc',
        'arguments': '*.less'
    },
}
CACHE_BACKEND = 'memcached://127.0.0.1:11211/'

HAYSTACK_SITECONF = 'astrobin.search_sites'
HAYSTACK_SEARCH_ENGINE = 'xapian'
HAYSTACK_XAPIAN_PATH = ASTROBIN_BASE_PATH + '/xapian_indexes'
HAYSTACK_DEFAULT_OPERATOR = 'AND'

#INTERNAL_IPS = ('88.115.221.254',) # for django-debug-toolbar: add own local IP to enable
INTERNAL_IPS = ('',)

MESSAGE_STORAGE = 'persistent_messages.storage.PersistentMessageStorage'

import djcelery
djcelery.setup_loader()

BROKER_HOST = 'localhost'
BROKER_PORT = 5672
BROKER_USER = 'astrobin'
BROKER_PASSWORD = 'h3C_U77a'
BROKER_VHOST = 'astrobin'

CELERY_RESULT_BACKEND = 'database'
CELERY_RESULT_DBURI = "mysql://astrobin:astrobin@localhost/astrobin"
CELERY_IMPORTS = ('astrobin.tasks', )
CELERY_QUEUES = {"default" : {"exchange":"default", "binding_key":"default"},
                 "plate_solve": {"exchange":"plate_solve", "binding_key":"plate_solve_key"}
                }
CELERY_DEFAULT_QUEUE = "default"
CELERY_ROUTES = {"astrobin.tasks.solve_image" : {"queue":"plate_solve", "routing_key":"plate_solve_key"},
                 "astrobin.tasks.image_solved_callback" : {"queue":"plate_solve", "routing_key":"plate_solve_key"},
                }

CELERYD_NODES = "w1 w2 w3 w4"
CELERYD_OPTS = "--time-limit=300 --concurrency=8 --verbosity=2 --loglevel=DEBUG"
CELERYD_CHDIR = ASTROBIN_BASE_PATH
CELERYD_LOG_FILE = "celeryd.log"
CELERYD_PID_FILE = "celeryd.pid"
CELERYD = ASTROBIN_BASE_PATH + "manage.py celeryd"

CELERYBEAT = ASTROBIN_BASE_PATH + "manage.py celerybeat"
CELERYBEAT_OPTS = "--verbosity=2 --loglevel=DEBUG"

ASTROBIN_ENABLE_SOLVING = True

PRIVATEBETA_ENABLE_BETA = False
PRIVATEBETA_ALWAYS_ALLOW_VIEWS = (
    'astrobin.views.help',
    'astrobin.views.faq',
    'astrobin.views.set_language',
)

ASTROBIN_USER='astrobin'


SIMBAD_QUERY_URL="http://simbad.u-strasbg.fr/simbad/sim-nameresolver?data=@,I.0,J,C.0,T,D,M,I&output.max=1&output=json&Ident="
SIMBAD_SEARCH_QUERY_URL="http://simbad.u-strasbg.fr/simbad/sim-nameresolver?data=@,I.0,J,C.0,T,D,M,I&output=json&Ident="

NOTIFICATION_LANGUAGE_MODULE = "astrobin.UserProfile"
