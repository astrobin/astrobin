# Django settings for astrobin project.
import os
from django.conf import global_settings
from django.utils.translation import ugettext_lazy as _

local_path = lambda path: os.path.join(os.path.dirname(__file__), path)

DEBUG = False
CACHE = not DEBUG
LOCAL_STATIC_STORAGE = True
TEMPLATE_DEBUG = DEBUG
MAINTENANCE_MODE = False
READONLY_MODE = False
MEDIA_VERSION = '71'
LONGPOLL_ENABLED = False
ADS_ENABLED = True
DONATIONS_ENABLED = False

ADMINS = (
    ('Salvatore Iovene', 'salvatore@astrobin.com'),
)

MANAGERS = ADMINS
SERVER_EMAIL = 'noreply@astrobin.com'
DEFAULT_FROM_EMAIL = 'AstroBin <noreply@astrobin.com>'
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_SUBJECT_PREFIX = '[AstroBin]'
EMAIL_HOST='127.0.0.1'
if DEBUG:
    EMAIL_PORT='1025'
else:
    EMAIL_PORT='25'
EMAIL_USE_TLS=False
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': os.environ['ASTROBIN_DATABASE_NAME'],         # Or path to database file if using sqlite3.
        'USER': os.environ['ASTROBIN_DATABASE_USER'],         # Not used with sqlite3.
        'PASSWORD': os.environ['ASTROBIN_DATABASE_PASSWORD'], # Not used with sqlite3.
        'HOST': os.environ['ASTROBIN_DATABASE_HOST'],         # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '5432',                                       # Set to empty string for default. Not used with sqlite3.
        'OPTIONS': {'autocommit': True},
    }
}

DEFAULT_CHARSET = 'utf-8'

ASTROBIN_BASE_URL = 'http://www.astrobin.com'
ASTROBIN_SHORT_BASE_URL = 'http://astrob.in'

ASTROBIN_BASE_PATH = os.path.dirname(__file__)
IMAGE_CACHE_DIRECTORY = '/webserver/www/imagecache/'
UPLOADS_DIRECTORY = IMAGE_CACHE_DIRECTORY

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/London'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'
LANGUAGE_COOKIE_NAME = 'astrobin_lang'

gettext = lambda s: s
LANGUAGES = (
    ('en', gettext('English')),
    ('it', gettext('Italian')),
    ('es', gettext('Spanish')),
    ('fr', gettext('French')),
    ('fi', gettext('Finnish')),
    ('de', gettext('German')),
    ('nl', gettext('Dutch')),
    ('tr', gettext('Turkish')),
    ('sq', gettext('Albanian')),
    #('pl', gettext('Polish')),
    ('pt-BR', gettext('Brazilian Portuguese')),
    ('el', gettext('Greek')),
)
MODELTRANSLATION_TRANSLATION_REGISTRY = 'astrobin.translation'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True
USE_L10N = True

SITE_ID = 1

# Make this unique, and don't share it with anybody.
SECRET_KEY = '4a*^ggw_5#w%tdf0q)=zozrw!avlts-h&&(--wy9x&p*c1l10G'

# Django storages
DEFAULT_FILE_STORAGE = 'astrobin.s3utils.ImageStorage'
AWS_ACCESS_KEY_ID = os.environ['ASTROBIN_AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['ASTROBIN_AWS_SECRET_ACCESS_KEY']
AWS_STORAGE_BUCKET_NAME = os.environ['ASTROBIN_AWS_STORAGE_BUCKET_NAME']
AWS_STORAGE_BUCKET_CNAME = AWS_STORAGE_BUCKET_NAME
AWS_S3_SECURE_URLS = False
AWS_QUERYSTRING_AUTH = False

from S3 import CallingFormat
AWS_CALLING_FORMAT = CallingFormat.SUBDOMAIN

# see http://developer.yahoo.com/performance/rules.html#expires
AWS_HEADERS = {
    'Expires': 'Fri, 9 May 2081 13:25:00 GMT+2'
}

S3_URL = 's3.amazonaws.com'
IMAGES_URL = os.environ['ASTROBIN_IMAGES_URL']
CDN_URL = os.environ['ASTROBIN_CDN_URL']

STATIC_ROOT = '/webserver/www/sitestatic'
if LOCAL_STATIC_STORAGE:
    STATIC_URL = '/sitestatic/'
else:
    STATIC_URL = CDN_URL + 'www/static/'

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = '/webserver/www/sitestatic/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
if LOCAL_STATIC_STORAGE:
    MEDIA_URL = '/media/'
else:
    MEDIA_URL = CDN_URL

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = STATIC_URL + '/admin/'


# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader',(
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),
)

MIDDLEWARE_CLASSES = [
    'django.middleware.http.ConditionalGetMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'pagination.middleware.PaginationMiddleware',
    'astrobin.middlewares.ProfileMiddleware',
#   'astrobin.middlewares.VaryOnLangCacheMiddleware',
    #'privatebeta.middleware.PrivateBetaMiddleware',
    'maintenancemode.middleware.MaintenanceModeMiddleware',
    'gadjo.requestprovider.middleware.RequestProvider',
#    'pipeline.middleware.MinifyHTMLMiddleware', Enable after dealing with the blank spaces everywhere
]

if DEBUG:
    MIDDLEWARE_CLASSES += [
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    ]

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

ROOT_URLCONF = 'astrobin.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    local_path('/templates'),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'astrobin.context_processors.privatebeta_enabled',
    'astrobin.context_processors.notices_count',
    'astrobin.context_processors.user_language',
    'astrobin.context_processors.user_profile',
    'astrobin.context_processors.user_scores',
    'astrobin.context_processors.common_variables',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'zinnia.context_processors.version',
)

INSTALLED_APPS = (
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.markup',
    'django.contrib.staticfiles',

    # AstroBin apps
    'common',
    'nested_comments',
    'astrobin',
    'rawdata',
    'astrobin_apps_images',
    'astrobin_apps_platesolving',
    'astrobin_apps_users',
    'astrobin_apps_donations',

    'toggleproperties',

    # Third party apps
    'registration',
    'haystack',
    'notification',
    'debug_toolbar',
    'persistent_messages',
    'djcelery',
    'gunicorn',
    'privatebeta',
    'south',
    'django.contrib.comments',
    'tagging',
    'mptt',
    'zinnia',
    'tinymce',
    'hitcount',
    'pagination',
    'avatar',
    'uni_form',
    'threaded_messages',
    'bootstrap_toolkit',
    'contact_form',
    'pipeline',
    'tastypie',
    'reviews',
    'actstream',
    'modeltranslation',
    'openid_provider',
    'paypal.standard.ipn',
    'subscription',
    'ember',
    'rest_framework',
    'rest_framework.authtoken',
    'easy_thumbnails',
    'endless_pagination',
    'dfp', # For Google DFP
)

LOGIN_REDIRECT_URL = '/'
ACCOUNT_ACTIVATION_DAYS = 7
AUTH_PROFILE_MODULE = 'astrobin.UserProfile'

FLICKR_API_KEY = os.environ['ASTROBIN_FLICKR_API_KEY']
FLICKR_SECRET  = os.environ['ASTROBIN_FLICKR_SECRET']

if CACHE:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': '127.0.0.1:11211',
        },
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        },
    }

JOHNNY_MIDDLEWARE_KEY_PREFIX='jc_astrobin'

HAYSTACK_SITECONF = 'astrobin.search_sites'
HAYSTACK_SEARCH_ENGINE = 'solr'
HAYSTACK_SOLR_URL = os.environ['ASTROBIN_HAYSTACK_SOLR_URL']
HAYSTACK_DEFAULT_OPERATOR = 'AND'
HAYSTACK_SEARCH_RESULTS_PER_PAGE = 70

#INTERNAL_IPS = ('88.115.221.254',) # for django-debug-toolbar: add own local IP to enable
if DEBUG:
    INTERNAL_IPS = ('127.0.0.1',)

MESSAGE_STORAGE = 'persistent_messages.storage.PersistentMessageStorage'

import djcelery
djcelery.setup_loader()

BROKER_HOST = 'localhost'
BROKER_PORT = 5672
BROKER_USER = os.environ['ASTROBIN_BROKER_USER']
BROKER_PASSWORD = os.environ['ASTROBIN_BROKER_PASSWORD']
BROKER_VHOST = 'astrobin'

CELERY_RESULT_BACKEND = 'database'
CELERY_RESULT_DBURI = os.environ['ASTROBIN_CELERY_RESULT_DBURI']
CELERY_IMPORTS = ('rawdata.tasks',)
CELERY_QUEUES = {"default" : {"exchange":"default", "binding_key":"default"},}
CELERY_DEFAULT_QUEUE = "default"

CELERYD_NODES = "w1 w2 w3 w4"
CELERYD_OPTS = "--time-limit=300 --concurrency=8 --verbosity=2 --loglevel=DEBUG"
CELERYD_CHDIR = ASTROBIN_BASE_PATH
CELERYD_LOG_FILE = "celeryd.log"
CELERYD_PID_FILE = "celeryd.pid"
CELERYD = ASTROBIN_BASE_PATH + "manage.py celeryd"

CELERYBEAT = ASTROBIN_BASE_PATH + "manage.py celerybeat"
CELERYBEAT_OPTS = "--verbosity=2 --loglevel=DEBUG"

ASTROBIN_ENABLE_SOLVING = True
ASTROBIN_PLATESOLVING_BACKEND = \
    'astrobin_apps_platesolving.backends.astrometry_net.solver.Solver'
ASTROMETRY_NET_API_KEY = os.environ['ASTROMETRY_NET_API_KEY']

PRIVATEBETA_ENABLE_BETA = False
PRIVATEBETA_ALWAYS_ALLOW_VIEWS = (
    'astrobin.views.help',
    'astrobin.views.faq',
    'astrobin.views.set_language',
)

ASTROBIN_USER='astrobin'


NOTIFICATION_LANGUAGE_MODULE = "astrobin.UserProfile"

ZINNIA_COPYRIGHT = 'AstroBin'
ZINNIA_MARKUP_LANGUAGE = 'html'
TINYMCE_JS_URL = MEDIA_URL + 'js/tiny_mce/tiny_mce.js'
TINYMCE_JS_ROOT = MEDIA_ROOT + '/js/tiny_mce'

HITCOUNT_KEEP_HIT_ACTIVE = { 'hours': 1 }
HITCOUNT_HITS_PER_IP_LIMIT = 0

AVATAR_GRAVATAR_BACKUP = False
AVATAR_DEFAULT_URL = 'images/astrobin-default-avatar.png?v=1'
AVATAR_AUTO_GENERATE_SIZES = (64,)

if LOCAL_STATIC_STORAGE:
    STATICFILES_STORAGE = 'pipeline.storage.PipelineStorage'
else:
    STATICFILES_STORAGE = 'astrobin.s3utils.StaticRootS3BotoStorage'
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)
STATICFILES_DIRS = (local_path('static/'),)

PIPELINE_CSS_COMPRESSOR = 'pipeline.compressors.cssmin.CssminCompressor'
PIPELINE_JS_COMPRESSOR = 'pipeline.compressors.jsmin.SlimItCompressor'

PIPELINE_CSS = {
    'screen': {
        'source_filenames': (
            'css/jquery-ui.css',
            'css/jquery-ui-astrobin/jquery-ui-1.8.17.custom.css',
            'css/ui.multiselect.css',
            'css/validationEngine.jquery.css',
            'css/facebox.css',
            'css/token-input.css',
            'css/jquery.multiselect.css',
            'css/jquery.qtip.css',

            'astrobin_apps_images/css/jquery.capty.css',
            'astrobin_apps_donations/css/astrobin_apps_donations.css',

            'css/reset.css',
            'css/bootstrap.css',
            'css/bootstrap-responsive.css',
            'css/astrobin.css',
        ),
        'output_filename': 'css/astrobin_pipeline_screen_v' + MEDIA_VERSION + '.css',
        'extra_content':  {
            'media': 'screen, projection',
        },
    },
}

# TODO: remove capty files
PIPELINE_JS = {
    'scripts': {
        'source_filenames': (
            'common/js/handlebars-1.0.rc.1.js',
            'common/js/ember-1.0.0-pre.2.js',

            'astrobin_apps_images/js/astrobin_apps_images.js',
            'astrobin_apps_images/js/jquery.capty.js',

            'js/jquery.i18n.js',
            'js/plugins/localization/jquery.localisation.js',
            'js/jquery.uniform.js',
            'js/jquery-ui-1.10.3.custom.min.js',
            'js/jquery-ui-timepicker-addon.js',
            'js/jquery.validationEngine-en.js',
            'js/jquery.validationEngine.js',
            'js/jquery.autoSuggest.js',
            'js/jquery.blockUI.js',
            'js/jquery.tmpl.1.1.1.js',
            'js/ui.multiselect.js',
            'js/facebox.js',
            'js/jquery.form.js',
            'js/jquery.tokeninput.js',
            'js/jquery.flot.js',
            'js/jquery.flot.pie.min.js',
            'js/jquery.cycle.all.js',
            'js/jquery.easing.1.3.js',
            'js/jquery.multiselect.js',
            'js/jquery.qtip.js',
            'js/jquery.stickytableheaders.js',
            'js/jquery.timeago.js',
            'js/respond.src.js',
            'js/masonry.js',
            'js/dfp.gpt.logger.override.js',
            'js/bootstrap.js',
            'js/astrobin.js',
        ),
        'output_filename': 'js/astrobin_pipeline_v' + MEDIA_VERSION + '.js',
    },
}

ACTSTREAM_SETTINGS = {
    'MODELS': (
        'auth.user',
        'astrobin.gear',
        'astrobin.telescope',
        'astrobin.camera',
        'astrobin.mount',
        'astrobin.filter',
        'astrobin.software',
        'astrobin.accessory',
        'astrobin.focalreducer',
        'astrobin.image',
        'astrobin.imagerevision',
        'rawdata.PublicDataPool',
        'nested_comments.nestedcomment',
        'reviews.revieweditem',
        'toggleproperties.toggleproperty',
    ),

}

PAYPAL_TEST = False

if PAYPAL_TEST:
    PAYPAL_RECEIVER_EMAIL = 'salvatore.iovene+paypal+sandbox+business@gmail.com'
else:
    PAYPAL_RECEIVER_EMAIL = 'salvatore.iovene@gmail.com'

SUBSCRIPTION_GRACE_PERIOD = 7
SUBSCRIPTION_PAYPAL_SETTINGS = {
    "business": PAYPAL_RECEIVER_EMAIL,
}

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAdminUser',),
    'PAGINATE_BY': 10,
    'FILTER_BACKEND': 'rest_framework.filters.DjangoFilterBackend',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication', # Useful for unit tests
    )
}

# http://docs.celeryproject.org/en/latest/django/unit-testing.html
TEST_RUNNER = 'djcelery.contrib.test_runner.CeleryTestSuiteRunner'

RAWDATA_ROOT = '/rawdata/files'

# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'null': {
            'level':'DEBUG',
            'class':'django.utils.log.NullHandler',
        },
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'standard'
        },
        'logfile': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': "logs/astrobin.txt",
            'maxBytes': 50000,
            'backupCount': 2,
            'formatter': 'standard',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django': {
            'handlers':['console'],
            'propagate': True,
            'level':'INFO',
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

THUMBNAIL_DEBUG = DEBUG
THUMBNAIL_ALWAYS_GENERATE = THUMBNAIL_DEBUG
THUMBNAIL_PROCESSORS = (
    # Default processors
    'easy_thumbnails.processors.colorspace',
    'easy_thumbnails.processors.autocrop',
    'easy_thumbnails.processors.scale_and_crop',
    'easy_thumbnails.processors.filters',

    # AstroBin processors
    'astrobin.thumbnail_processors.rounded_corners',
    'astrobin.thumbnail_processors.invert',
    'astrobin.thumbnail_processors.watermark',
    'astrobin.thumbnail_processors.histogram',
)
THUMBNAIL_ALIASES = {
    '': {
        # Main image thumbnails
        # TODO: verify what happens with animated GIF
        'real': {'size': (16536, 16536), 'watermark': True},
        'real_inverted': {'size': (16536, 16536), 'invert': True, 'watermark': True},

        'hd': {'size': (1824, 0), 'crop': False, 'watermark': True},
        'hd_inverted': {'size': (1824, 0), 'crop': False, 'invert': True, 'watermark': True},

        'regular': {'size': (620, 0), 'crop': False, 'watermark': True},
        'regular_inverted': {'size': (620, 0), 'crop': False, 'invert': True, 'watermark': True},

        'gallery': {'size': (130, 130), 'crop': 'smart', 'rounded': True, 'quality': 80},
        'gallery_inverted': {'size': (130, 130), 'crop': 'smart', 'rounded': True, 'quality': 80, 'invert': True},
        'thumb': {'size': (80, 80), 'crop': True, 'rounded': 'smart', 'quality': 60},

        # Tricks
        'histogram': {'size': (274, 120), 'histogram': True},

        # IOTD
        'iotd': {'size': (780, 180), 'crop': 'smart', 'watermark': True},

        # Activity stream
        'act_target': {'size': (226, 62), 'crop': 'smart', 'quality': 80},
        'act_object': {'size': (226, 226), 'crop': 'smart', 'quality': 80},
    },
}
THUMBNAIL_QUALITY = 100
THUMBNAIL_SUBDIR = 'thumbs'
THUMBNAIL_DEFAULT_STORAGE = DEFAULT_FILE_STORAGE

ENDLESS_PAGINATION_PER_PAGE = 35
ENDLESS_PAGINATION_LOADING = '<img src="' + STATIC_URL + 'common/images/ajax-loader-bar.gif" alt="..." />'

TOGGLEPROPERTIES = {
    "bookmark": {
        "property_tooltip_on": _("Remove from bookmarks"),
        "property_tooltip_off": _("Bookmark"),
        "property_icon": "icon-bookmark",
    },

    "like": {
        "property_label_on": _("Unlike"),
        "property_label_off": _("Like"),
        "property_tooltip_on": _("Unlike"),
        "property_tooltip_off": _("Like"),
        "property_icon": "icon-thumbs-up",
    },

    "follow": {
        "property_tooltip_on": _("Stop following"),
        "property_tooltip_off": _("Follow"),
        "property_icon": "icon-plus",
    }
}
