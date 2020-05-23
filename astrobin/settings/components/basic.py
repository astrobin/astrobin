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
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'default.key').strip()
SITE_ID = 1

TESTING = os.environ.get("TESTING", 'false').strip() == 'true' or len(sys.argv) > 1 and sys.argv[1] == 'test'
DEBUG = os.environ.get('DEBUG', 'true').strip() == 'true'
INTERNAL_IPS = ['127.0.0.1', '172.18.0.1'] # localhost and docker gateway

MAINTENANCE_MODE = False
MAINTENANCE_LOCKFILE_PATH = 'maintenance-lock.file'

READONLY_MODE = os.environ.get("READONLY_MODE", 'false').strip() == 'true'
LONGPOLL_ENABLED = False

ALLOWED_HOSTS = ['*']
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760

ADS_ENABLED = os.environ.get('ADS_ENABLED', 'false').strip() == 'true'
DONATIONS_ENABLED = os.environ.get('DONATIONS_ENABLED', 'false').strip() == 'true'
PREMIUM_ENABLED = os.environ.get('PREMIUM_ENABLED', 'true').strip() == 'true'

BASE_URL = os.environ.get('BASE_URL', 'http://localhost').strip()
SHORT_BASE_URL = os.environ.get('SHORT_BASE_URL', BASE_URL).strip()
BASE_PATH = os.path.dirname(__file__)

MIN_INDEX_TO_LIKE = float(os.environ.get('MIN_INDEX_TO_LIKE', '1.00').strip())
GOOGLE_ANALYTICS_ID = os.environ.get('GOOGLE_ANALYTICS_ID', 'invalid').strip()
GOOGLE_ADS_ID = os.environ.get('GOOGLE_ADS_ID', 'invalid').strip()

ROOT_URLCONF = 'astrobin.urls'

ALLOWED_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif')
ALLOWED_FITS_IMAGE_EXTENSIONS = ('xisf', 'fits', 'fit', 'fts')
ALLOWED_UNCOMPRESSED_SOURCE_EXTENSIONS = ALLOWED_FITS_IMAGE_EXTENSIONS + ('psd', 'tiff')

GEOIP_PATH = os.path.abspath(os.path.dirname(__name__)) + "/astrobin/geoip2"

CORS_ORIGIN_ALLOW_ALL = False
CORS_ORIGIN_WHITELIST = (
    'app.astrobin.com'
)
