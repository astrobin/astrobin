import os

local_path = lambda path: os.path.join(os.path.dirname(__file__), path)


AWS_S3_ENABLED = os.environ['AWS_S3_ENABLED'] == "true"
if AWS_S3_ENABLED:
    S3_URL = 's3.amazonaws.com'
    IMAGES_URL = os.environ['IMAGES_URL']

    MEDIA_URL = os.environ['CDN_URL']
    STATIC_URL = MEDIA_URL + 'static/'

    AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
    AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
    AWS_STORAGE_BUCKET_NAME = os.environ['AWS_STORAGE_BUCKET_NAME']
    AWS_STORAGE_BUCKET_CNAME = AWS_STORAGE_BUCKET_NAME
    AWS_S3_SECURE_URLS = True
    AWS_QUERYSTRING_AUTH = False

    AWS_S3_CALLING_FORMAT = 'boto.s3.connection.OrdinaryCallingFormat'
    AWS_S3_HOST = 's3.amazonaws.com'

    # see http://developer.yahoo.com/performance/rules.html#expires
    AWS_HEADERS = {
        'Expires': 'Wed, 31 Dec 2036 23:59:59 GMT'
    }

LOCAL_STATIC_STORAGE = os.environ['LOCAL_STATIC_STORAGE'] == "true"
if LOCAL_STATIC_STORAGE:
    STATIC_URL = '/media/static/'
    STATICFILES_STORAGE = 'pipeline.storage.PipelineStorage'
else:
    STATICFILES_STORAGE = 'astrobin.s3utils.StaticRootS3BotoStorage'

DEFAULT_FILE_STORAGE = 'astrobin.s3utils.ImageStorage'
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'pipeline.finders.PipelineFinder',
)
STATICFILES_DIRS = (local_path('../static'),)

MESSAGE_STORAGE = 'persistent_messages.storage.PersistentMessageStorage'
