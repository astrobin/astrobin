# Django settings for astrobin project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Salvatore Iovene', 'salvatore@iovene.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'sqlite3'    # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'astrobin.db'  # Or path to database file if using sqlite3.
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = '/var/www/astrobin/static'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/static/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '4a*^ggw_5#w%tdf0q)=zozrw!avlts-h&&(--wy9x&p*c1l10g'
S3_ACCESS_KEY = 'AKIAJ46VGDGOKKHGGOAQ'
S3_SECRET_KEY = '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'
S3_IMAGES_BUCKET = 'astrobin_images'
S3_RESIZED_IMAGES_BUCKET = 'astrobin_resized_image'
S3_THUMBNAILS_BUCKET = 'astrobin_thumbnails'
S3_SMALL_THUMBNAILS_BUCKET = 'astrobin_small_thumbnails'
S3_INVERTED_BUCKET = 'astrobin_inverted'
S3_RESIZED_INVERTED_BUCKET = 'astrobin_resized_inverted'
S3_ABPOD_BUCKET = 'astrobin_abpod'
S3_AVATARS_BUCKET = 'astrobin_avatars'
S3_URL = 's3.amazonaws.com'

RESIZED_IMAGE_SIZE = 720
THUMBNAIL_SIZE = 230
SMALL_THUMBNAIL_SIZE = 100
ABPOD_SIZE = 350

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'astrobin.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    '/var/www/astrobin/templates'
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
    'django.core.context_processors.auth',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'bin',
    'django.contrib.admin',
    'registration',
    'ajax_select',
)

LOGIN_REDIRECT_URL = '/'
ACCOUNT_ACTIVATION_DAYS = 7
AUTH_PROFILE_MODULE = 'bin.UserProfile'

AJAX_LOOKUP_CHANNELS = {
    'telescope' : ('bin.lookups', 'TelescopeLookup'),
}

FLICKR_API_KEY = '1f44b18e230b8c9816a39d9b34c3318d'
FLICKR_SECRET  = 'd5fdb83e9aa995fc'

