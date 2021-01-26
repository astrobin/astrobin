import os

local_path = lambda path: os.path.join(os.path.dirname(__file__), path)


AWS_S3_ENABLED = os.environ.get('AWS_S3_ENABLED', 'false').strip() == "true"
if AWS_S3_ENABLED:
    AWS_S3_CUSTOM_DOMAIN = os.environ.get('AWS_S3_CUSTOM_DOMAIN', 'cdn.astrobin.com').strip()
    MEDIA_ROOT = '/'
    MEDIA_URL = 'https://%s/' % AWS_S3_CUSTOM_DOMAIN

    STATIC_ROOT = 'static/'
    STATIC_URL = MEDIA_URL + 'static/'

    S3_URL = 's3.amazonaws.com'
    AWS_DEFAULT_REGION = 'us-east-1'
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', 'invalid').strip()
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', 'invalid').strip()
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', 'cdn.astrobin.com').strip()
    AWS_STORAGE_BUCKET_CNAME = AWS_STORAGE_BUCKET_NAME
    AWS_S3_SECURE_URLS = True
    AWS_QUERYSTRING_AUTH = False
    AWS_DEFAULT_ACL = 'public-read'
    AWS_S3_OBJECT_PARAMETERS = {
        'Expires': 'Wed, 31 Dec 2036 23:59:59 GMT'
    }
    AWS_S3_ENDPOINT_URL = 'https://s3.amazonaws.com'
else:
    MEDIA_ROOT = '/media/'
    MEDIA_URL = BASE_URL + MEDIA_ROOT

    STATIC_ROOT = MEDIA_ROOT
    STATIC_URL = MEDIA_URL + 'static/'

# Normalize
if not MEDIA_URL.endswith('/'):
    MEDIA_URL = '%s/' % MEDIA_URL

IMAGES_URL = MEDIA_URL
UPLOADS_DIRECTORY = MEDIA_ROOT
ADMIN_MEDIA_PREFIX = STATIC_URL + 'admin/'

LOCAL_STATIC_STORAGE = os.environ.get('LOCAL_STATIC_STORAGE', 'true').strip() == "true"
if LOCAL_STATIC_STORAGE:
    STATIC_ROOT = STATIC_URL = '/media/static/'
    STATICFILES_STORAGE = 'astrobin.s3utils.StaticRootLocalStorage'
else:
    STATICFILES_STORAGE = 'astrobin.s3utils.StaticRootS3BotoStorage'

DEFAULT_FILE_STORAGE = 'astrobin.s3utils.ImageStorage'
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'pipeline.finders.PipelineFinder',
)

MESSAGE_STORAGE = 'persistent_messages.storage.PersistentMessageStorage'

FILE_UPLOAD_HANDLERS = (
    "progressbarupload.uploadhandler.ProgressBarUploadHandler",
    "django.core.files.uploadhandler.MemoryFileUploadHandler",
    "django.core.files.uploadhandler.TemporaryFileUploadHandler",
)

PROGRESSBARUPLOAD_INCLUDE_JQUERY = False

