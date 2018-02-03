import sys
import os

DEFAULT_CHARSET = 'utf-8'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/London'

# Make this unique, and don't share it with anybody.
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
SITE_ID = 1


TESTING = len(sys.argv) > 1 and sys.argv[1] == 'test'
DEBUG = os.environ['DEBUG'] == "true"
DEBUG_PROPAGATE_EXCEPTIONS = DEBUG
INTERNAL_IPS = ['127.0.0.1', '172.18.0.1'] # localhost and docker gateway

MAINTENANCE_MODE = False
READONLY_MODE = False
LONGPOLL_ENABLED = False

ALLOWED_HOSTS = ['*']

ADS_ENABLED = os.environ['ADS_ENABLED'] == 'true'
DONATIONS_ENABLED = os.environ['DONATIONS_ENABLED'] == 'true'
PREMIUM_ENABLED = os.environ['PREMIUM_ENABLED'] == 'true'

MEDIA_VERSION = '224'

BASE_URL = os.environ['BASE_URL']
SHORT_BASE_URL = os.environ['SHORT_BASE_URL']
BASE_PATH = os.path.dirname(__file__)

MIN_INDEX_TO_LIKE = float(os.environ['MIN_INDEX_TO_LIKE'])
GOOGLE_ANALYTICS_ID = os.environ['GOOGLE_ANALYTICS_ID']

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = MEDIA_URL = '/media/'
STATIC_ROOT = STATIC_URL = MEDIA_ROOT + 'static/'

IMAGES_URL = MEDIA_URL
IMAGE_CACHE_DIRECTORY = MEDIA_ROOT + 'imagecache/'
UPLOADS_DIRECTORY = MEDIA_ROOT

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = STATIC_URL + 'admin/'


ROOT_URLCONF = 'astrobin.urls'

