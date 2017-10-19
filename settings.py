# Django settings for astrobin project.
import sys
import os
from django.conf import global_settings
from django.utils.translation import ugettext_lazy as _

local_path = lambda path: os.path.join(os.path.dirname(__file__), path)

TESTING = len(sys.argv) > 1 and sys.argv[1] == 'test'
DEBUG = os.environ['ASTROBIN_DEBUG'] == "true"
try:
    DEBUG_TOOLBAR = DEBUG and os.environ['ASTROBIN_DEBUG_TOOLBAR'] == 'true'
except KeyError:
    DEBUG_TOOLBAR = False
CACHE = not DEBUG
ALLOWED_HOSTS = ['*']
TEMPLATE_DEBUG = DEBUG
MAINTENANCE_MODE = False
READONLY_MODE = False
MEDIA_VERSION = '196'
LONGPOLL_ENABLED = False
ADS_ENABLED = True
DONATIONS_ENABLED = False
PREMIUM_ENABLED = True

if TESTING:
    DEBUG = False
    TEMPLATE_DEBUG = False
    CACHE = False
    AWS_S3_ENABLED = False
    LOCAL_STATIC_STORAGE = True
    PASSWORD_HASHERS = (
        'django.contrib.auth.hashers.MD5PasswordHasher',
    )
else:
    AWS_S3_ENABLED = os.environ['ASTROBIN_AWS_S3_ENABLED'] == "true"
    LOCAL_STATIC_STORAGE = os.environ['ASTROBIN_LOCAL_STATIC_STORAGE'] == "true"

ADMINS = (
    ('Salvatore Iovene', 'salvatore@astrobin.com'),
)

MANAGERS = ADMINS
SERVER_EMAIL = 'noreply@astrobin.com'
DEFAULT_FROM_EMAIL = 'AstroBin <noreply@astrobin.com>'
EMAIL_HOST_USER = os.environ['ASTROBIN_EMAIL_HOST_USER']
EMAIL_HOST_PASSWORD = os.environ['ASTROBIN_EMAIL_HOST_PASSWORD']
EMAIL_SUBJECT_PREFIX = '[AstroBin]'
EMAIL_HOST = os.environ['ASTROBIN_EMAIL_HOST']
EMAIL_PORT = os.environ['ASTROBIN_EMAIL_PORT']
EMAIL_USE_TLS= os.environ['ASTROBIN_EMAIL_USE_TLS'] == "true"
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

if not TESTING:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': os.environ['ASTROBIN_DATABASE_NAME'],
            'USER': os.environ['ASTROBIN_DATABASE_USER'],
            'PASSWORD': os.environ['ASTROBIN_DATABASE_PASSWORD'],
            'HOST': os.environ['ASTROBIN_DATABASE_HOST'],
            'PORT': '5432'
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'astrobin_test_db',
        }
    }

DEFAULT_CHARSET = 'utf-8'

ASTROBIN_BASE_URL = 'http://www.astrobin.com'
ASTROBIN_SHORT_BASE_URL = 'http://astrob.in'

ASTROBIN_BASE_PATH = os.path.dirname(__file__)

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
    ('pl', gettext('Polish')),
    ('pt-BR', gettext('Brazilian Portuguese')),
    ('el', gettext('Greek')),
    ('ru', gettext('Russian')),
    ('ar', gettext('Arabic')),
    ('ja', gettext('Japanese')),
)
MODELTRANSLATION_TRANSLATION_REGISTRY = 'astrobin.translation'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True
USE_L10N = True

SITE_ID = 1

# Make this unique, and don't share it with anybody.
SECRET_KEY = os.environ['ASTROBIN_DJANGO_SECRET_KEY']

# Django storages
DEFAULT_FILE_STORAGE = 'astrobin.s3utils.ImageStorage'

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = '/var/www/media/'
MEDIA_URL = '/media/'

STATIC_ROOT = MEDIA_ROOT + 'static/'
STATIC_URL = MEDIA_URL + 'static/'

IMAGES_URL = MEDIA_URL + 'images/'
IMAGE_CACHE_DIRECTORY = MEDIA_ROOT + 'imagecache/'
UPLOADS_DIRECTORY = MEDIA_ROOT + 'images/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = STATIC_URL + '/admin/'

if AWS_S3_ENABLED:
    S3_URL = 's3.amazonaws.com'
    IMAGES_URL = os.environ['ASTROBIN_IMAGES_URL']

    MEDIA_URL = os.environ['ASTROBIN_CDN_URL']

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
        'Expires': 'Wed, 31 Dec 2036 23:59:59 GMT'
    }

if LOCAL_STATIC_STORAGE:
    STATIC_URL = '/media/static/'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader',(
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),
)

MIDDLEWARE_CLASSES = []
if DEBUG_TOOLBAR:
    MIDDLEWARE_CLASSES += [
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    ]
MIDDLEWARE_CLASSES += [
    'django.middleware.http.ConditionalGetMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'pagination.middleware.PaginationMiddleware',
    'astrobin.middlewares.ProfileMiddleware',
#   'astrobin.middlewares.VaryOnLangCacheMiddleware',
    'maintenancemode.middleware.MaintenanceModeMiddleware',
    'gadjo.requestprovider.middleware.RequestProvider',
#    'pipeline.middleware.MinifyHTMLMiddleware', Enable after dealing with the blank spaces everywhere
    'pybb.middleware.PybbMiddleware',
]
if not TESTING and not DEBUG:
    MIDDLEWARE_CLASSES += [
        'django.middleware.locale.LocaleMiddleware',
        'django.middleware.gzip.GZipMiddleware',
    ]

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

ROOT_URLCONF = 'astrobin.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    local_path('astrobin/templates'),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'astrobin.context_processors.notices_count',
    'astrobin.context_processors.user_language',
    'astrobin.context_processors.user_profile',
    'astrobin.context_processors.user_scores',
    'astrobin.context_processors.common_variables',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'pybb.context_processors.processor',
)

INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',

    # Third party apps
    'registration',
    'haystack',
    'notification',
    'persistent_messages',
    'djcelery',
    'gunicorn',
    'django_comments',
    'tagging',
    'mptt',
    'tinymce',
    'hitcount',
    'pagination',
    'avatar',
    'crispy_forms',
    'threaded_messages',
    'bootstrap_toolkit',
    'contact_form',
    'pipeline',
    'tastypie',
    'reviews',
    'actstream',
    'modeltranslation',
    'paypal.standard.ipn',
    'subscription',
    'ember',
    'rest_framework',
    'rest_framework.authtoken',
    'easy_thumbnails',
    'el_pagination',
    'dfp', # For Google DFP
    'django_user_agents',
    'pybb', # Forum
    'markup_deprecated',
    'sanitizer',

    # AstroBin apps
    'astrobin.apps.AstroBinAppConfig',
    'common',
    'nested_comments',
    'rawdata',
    'astrobin_apps_images',
    'astrobin_apps_platesolving',
    'astrobin_apps_users',
    'astrobin_apps_donations',
    'astrobin_apps_premium',
    'astrobin_apps_notifications',
    'astrobin_apps_groups',
    'astrobin_apps_iotd',
    'toggleproperties',
]
if DEBUG_TOOLBAR:
    INSTALLED_APPS += ['debug_toolbar',]

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

HAYSTACK_DEFAULT_OPERATOR = 'AND'
HAYSTACK_SEARCH_RESULTS_PER_PAGE = 70
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
        'URL': os.environ['ASTROBIN_HAYSTACK_SOLR_URL'],
        'EXCLUDED_INDEXES': [
            'threaded_messages.search_indexes.Thread',
            'threaded_messages.search_indexes.ThreadIndex',
        ],
    },
}


#INTERNAL_IPS = ('88.115.221.254',) # for django-debug-toolbar: add own local IP to enable
if DEBUG_TOOLBAR:
    INTERNAL_IPS = ('127.0.0.2', '10.0.0.2',)
    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK" : 'astrobin.debug_toolbar.show_debug_toolbar',
    }

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
    'pipeline.finders.PipelineFinder',
)
STATICFILES_DIRS = (local_path('astrobin/static/'),)

PIPELINE = {
    'PIPELINE_ENABLED': not DEBUG,
    'JAVASCRIPT': {
        'scripts': {
            'source_filenames': (
                'common/js/handlebars-1.0.rc.1.js',
                'common/js/ember-1.0.0-pre.2.js',
                'common/fancybox/jquery.fancybox.js/',

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
                'js/dfp.gpt.logger.override.js',
                'js/bootstrap.js',
                'js/astrobin.js',
            ),
            'output_filename': 'js/astrobin_pipeline_v' + MEDIA_VERSION + '.js',
        }
    },
    'STYLESHEETS': {
        'screen': {
            'source_filenames': (
                'css/jquery-ui.css',
                'css/jquery-ui-astrobin/jquery-ui-1.8.17.custom.css',
                'css/ui.multiselect.css',
                'css/validationEngine.jquery.css',
                'css/token-input.css',
                'css/jquery.multiselect.css',
                'css/jquery.qtip.css',

                'wysibb/theme/default/wbbtheme.css',

                'astrobin_apps_images/css/jquery.capty.css',
                'astrobin_apps_donations/css/astrobin_apps_donations.css',
                'astrobin_apps_premium/css/astrobin_apps_premium.css',

                'css/reset.css',
                'css/bootstrap.css',
                'css/bootstrap-responsive.css',

                'common/fancybox/jquery.fancybox.css',

                'css/astrobin.css',
                'css/astrobin-mobile.css',
            ),
            'output_filename': 'css/astrobin_pipeline_screen_v' + MEDIA_VERSION + '.css',
            'extra_content':  {
                'media': 'screen, projection',
            },
        }
    },
    'CSS_COMPRESSOR': 'pipeline.compressors.cssmin.CssminCompressor',
    'JS_COMPRESSOR': 'pipeline.compressors.jsmin.SlimItCompressor'
}

PAYPAL_TEST = DEBUG
PAYPAL_DEBUG = PAYPAL_TEST

if PAYPAL_TEST:
    PAYPAL_RECEIVER_EMAIL = 'salvatore.iovene+paypal+sandbox+business@gmail.com'
else:
    PAYPAL_RECEIVER_EMAIL = 'salvatore.iovene@gmail.com'

# Used for the "Cancel subscription" link
PAYPAL_MERCHANT_ID = os.environ['ASTROBIN_PAYPAL_MERCHANT_ID']

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

RAWDATA_ROOT = os.environ['ASTROBIN_RAWDATA_ROOT']

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
            'class':'logging.NullHandler',
        },
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'standard'
        },
        'logfile': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': "/var/log/astrobin/debug.log",
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

if TESTING:
    import logging
    logging.disable(logging.CRITICAL)

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
AVAILABLE_IMAGE_MODS = ('inverted',)
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
        'collection': {'size': (123, 123), 'crop': 'smart', 'quality': 60},
        'thumb': {'size': (80, 80), 'crop': True, 'rounded': 'smart', 'quality': 60},

        # Tricks
        'histogram': {'size': (274, 120), 'histogram': True},

        # IOTD
        'iotd': {'size': (1000, 380), 'crop': 'smart', 'watermark': True},
        'iotd_candidate': {'size': (960, 0), 'crop': 'smart', 'watermark': False},

        # Activity stream
        'story': {'size': (460, 320), 'crop': 'smart', 'quality': 90},

        # Duckduckgo
        'duckduckgo': {'size': (250, 200), 'crop': 'smart', 'quality': 80},
        'duckduckgo_small': {'size': (113, 90), 'crop': 'smart', 'quality': 80},
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
        "property_tooltip_as_bootstrap": False,
        "property_icon": "icon-bookmark",
    },

    "like": {
        "property_label_on": _("Unlike"),
        "property_label_off": _("Like"),
        "property_tooltip_on": _("Unlike"),
        "property_tooltip_off": _("Like"),
        "property_tooltip_as_bootstrap": False,
        "property_icon": "icon-thumbs-up",
    },

    "follow": {
        "property_tooltip_on": _("Stop following"),
        "property_tooltip_off": _("Follow"),
        "property_tooltip_as_bootstrap": False,
        "property_icon": "icon-plus",
    }
}

PYBB_DEFAULT_TITLE = "AstroBin Forum"
PYBB_DEFAULT_FROM_EMAIL = "AstroBin Forum <noreply@astrobin.com>"
PYBB_NICE_URL = True
PYBB_PERMISSION_HANDLER = "astrobin.permissions.CustomForumPermissions"
PYBB_ATTACHMENT_ENABLE = False
PYBB_PROFILE_RELATED_NAME = 'userprofile'
PYBB_SMILES_PREFIX = 'emoticons/'
PYBB_SMILES = {
    '&gt;_&lt;': 'mad.png',
    ':.(': 'sad.png',
    'o_O': 'smartass.png',
    '8)': 'sunglasses.png',
    ':D': 'grin.png',
    ':(': 'sad.png',
    ':O': 'surprised.png',
    '-_-': 'sorry.png',
    ':)': 'smile.png',
    ':P': 'tongue.png',
    ';)': 'blink.png',
    '&lt;3': 'love.png',
}
PYBB_TOPIC_PAGE_SIZE = 25
PYBB_FORUM_PAGE_SIZE = 50

def pybb_premoderation(user, post):
    index = user.userprofile.get_scores()['user_scores_index']
    return index >= 1.00

PYBB_PREMODERATION = pybb_premoderation

if TESTING:
    PREMIUM_MAX_IMAGES_FREE = 20
    PREMIUM_MAX_IMAGES_LITE = 20
else:
    PREMIUM_MAX_IMAGES_FREE = 10
    PREMIUM_MAX_IMAGES_LITE = 12

SANITIZER_ALLOWED_TAGS = ['b', 'i', 'strong', 'em', 'a', 'img']
SANITIZER_ALLOWED_ATTRIBUTES = ['href', 'target', 'src']


IOTD_SUBMISSION_WINDOW_DAYS = 3
IOTD_SUBMISSION_MAX_PER_DAY = 3

IOTD_REVIEW_WINDOW_DAYS = 5
IOTD_REVIEW_MAX_PER_DAY = 3

IOTD_JUDGEMENT_WINDOW_DAYS = 7
IOTD_JUDGEMENT_MAX_PER_DAY = 1
IOTD_JUDGEMENT_MAX_FUTURE_DAYS = 7
IOTD_JUDGEMENT_MAX_FUTURE_PER_JUDGE = 2

IOTD_SHOW_CHOOSING_JUDGE = False

MIN_INDEX_TO_LIKE = float(os.environ['ASTROBIN_MIN_INDEX_TO_LIKE'])
