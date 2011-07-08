"""
Incorporated from django-storages, copyright all of those listed in:
http://code.welldev.org/django-storages/src/tip/AUTHORS
"""
import os
import mimetypes

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from django.conf import settings
from django.core.files.base import File
from django.core.files.storage import Storage
from django.core.exceptions import ImproperlyConfigured

try:
    from boto.s3.connection import S3Connection
    from boto.exception import S3ResponseError
    from boto.s3.key import Key
except ImportError:
    raise ImproperlyConfigured, "Could not load Boto's S3 bindings.\
    \nSee http://code.google.com/p/boto/"

ACCESS_KEY_NAME = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
SECRET_KEY_NAME = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
HEADERS = getattr(settings, 'AWS_HEADERS', {})
STORAGE_BUCKET_NAME = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
STORAGE_BUCKET_CNAME = getattr(settings, 'AWS_STORAGE_BUCKET_CNAME', None)
AUTO_CREATE_BUCKET = getattr(settings, 'AWS_AUTO_CREATE_BUCKET', True)
DEFAULT_ACL = getattr(settings, 'AWS_DEFAULT_ACL', 'public-read')
QUERYSTRING_AUTH = getattr(settings, 'AWS_QUERYSTRING_AUTH', True)
QUERYSTRING_EXPIRE = getattr(settings, 'AWS_QUERYSTRING_EXPIRE', 3600)
LOCATION = getattr(settings, 'AWS_LOCATION', '')
IS_GZIPPED = getattr(settings, 'AWS_IS_GZIPPED', False)
GZIP_CONTENT_TYPES = getattr(settings, 'GZIP_CONTENT_TYPES', (
    'text/css',
    'application/javascript',
    'application/x-javascript'
))

if IS_GZIPPED:
    from gzip import GzipFile

class S3BotoStorage(Storage):
    """Amazon Simple Storage Service using Boto"""

    def __init__(self, bucket=STORAGE_BUCKET_NAME,
                       bucket_cname=STORAGE_BUCKET_CNAME,
                       access_key=None, secret_key=None, acl=DEFAULT_ACL,
                       headers=HEADERS, gzip=IS_GZIPPED,
                       gzip_content_types=GZIP_CONTENT_TYPES,
                       querystring_auth=QUERYSTRING_AUTH,
                       force_no_ssl=False):
        self.bucket_name = bucket
        self.bucket_cname = bucket_cname
        self.acl = acl
        self.headers = headers
        self.gzip = gzip
        self.gzip_content_types = gzip_content_types
        self.querystring_auth = querystring_auth
        self.force_no_ssl = force_no_ssl
        # This is called as chunks are uploaded to S3. Useful for getting
        # around limitations in eventlet for things like gunicorn.
        self.s3_callback_during_upload = None

        if not access_key and not secret_key:
            access_key, secret_key = self._get_access_keys()

        self.connection = S3Connection(access_key, secret_key)

    @property
    def bucket(self):
        if not hasattr(self, '_bucket'):
            self._bucket = self._get_or_create_bucket(self.bucket_name)
        return self._bucket

    def _get_access_keys(self):
        access_key = ACCESS_KEY_NAME
        secret_key = SECRET_KEY_NAME
        if (access_key or secret_key) and (not access_key or not secret_key):
            access_key = os.environ.get(ACCESS_KEY_NAME)
            secret_key = os.environ.get(SECRET_KEY_NAME)

        if access_key and secret_key:
            # Both were provided, so use them
            return access_key, secret_key

        return None, None

    def _get_or_create_bucket(self, name):
        """Retrieves a bucket if it exists, otherwise creates it."""
        try:
            return self.connection.get_bucket(name)
        except S3ResponseError, e:
            if AUTO_CREATE_BUCKET:
                return self.connection.create_bucket(name)
            raise ImproperlyConfigured, ("Bucket specified by "
            "AWS_STORAGE_BUCKET_NAME does not exist. Buckets can be "
            "automatically created by setting AWS_AUTO_CREATE_BUCKET=True")

    def _clean_name(self, name):
        # Useful for windows' paths
        return os.path.normpath(name).replace('\\', '/')

    def _compress_content(self, content):
        """Gzip a given string."""
        zbuf = StringIO()
        zfile = GzipFile(mode='wb', compresslevel=6, fileobj=zbuf)
        zfile.write(content.read())
        zfile.close()
        content.file = zbuf
        return content

    def _open(self, name, mode='rb'):
        name = self._clean_name(name)
        return S3BotoStorageFile(name, mode, self)

    def _save(self, name, content):
        name = self._clean_name(name)

        if callable(self.headers):
            headers = self.headers(name, content)
        else:
            headers = self.headers

        if hasattr(content.file, 'content_type'):
            content_type = content.file.content_type
        else:
            content_type = mimetypes.guess_type(name)[0] or "application/x-octet-stream"

        if self.gzip and content_type in self.gzip_content_types:
            content = self._compress_content(content)
            headers.update({'Content-Encoding': 'gzip'})

        headers.update({
            'Content-Type': content_type,
            'Content-Length' : len(content),
        })

        content.name = name
        k = self.bucket.get_key(name)
        if not k:
            k = self.bucket.new_key(name)
        k.set_contents_from_file(content, headers=headers, policy=self.acl,
                                 cb=self.s3_callback_during_upload)
        return name

    def delete(self, name):
        name = self._clean_name(name)
        self.bucket.delete_key(name)

    def exists(self, name):
        name = self._clean_name(name)
        k = Key(self.bucket, name)
        return k.exists()

    def listdir(self, name):
        name = self._clean_name(name)
        return [l.name for l in self.bucket.list() if not len(name) or l.name[:len(name)] == name]

    def size(self, name):
        name = self._clean_name(name)
        return self.bucket.get_key(name).size

    def url(self, name):
        name = self._clean_name(name)
        if self.bucket.get_key(name) is None:
            return ''
        return self.bucket.get_key(name).generate_url(QUERYSTRING_EXPIRE,
                                                      method='GET',
                                                      query_auth=self.querystring_auth,
                                                      force_http=self.force_no_ssl)

    def url_as_attachment(self, name, filename=None):
        name = self._clean_name(name)

        if filename:
            disposition = 'attachment; filename="%s"' % filename
        else:
            disposition = 'attachment;'

        response_headers = {
            'response-content-disposition': disposition,
        }

        return self.connection.generate_url(QUERYSTRING_EXPIRE, 'GET',
                                            bucket=self.bucket.name, key=name,
                                            query_auth=True,
                                            force_http=self.force_no_ssl,
                                            response_headers=response_headers)

    def get_available_name(self, name):
        """ Overwrite existing file with the same name. """
        name = self._clean_name(name)
        return name

class S3BotoStorage_AllPublic(S3BotoStorage):
    """
    Same as S3BotoStorage, but defaults to uploading everything with a
    public acl. This has two primary beenfits:
    
    1) Non-encrypted requests just make a lot better sense for certain things
       like profile images. Much faster, no need to generate S3 auth keys.
    2) Since we don't have to hit S3 for auth keys, this backend is much
       faster than S3BotoStorage, as it makes no attempt to validate whether
       keys exist.
       
    WARNING: This backend makes absolutely no attempt to verify whether the
    given key exists on self.url(). This is much faster, but be aware.
    """
    def __init__(self, *args, **kwargs):
        super(S3BotoStorage_AllPublic, self).__init__(acl='public-read',
                                                      querystring_auth=False,
                                                      force_no_ssl=True,
                                                      *args, **kwargs)

    def url(self, name):
        """
        Since we assume all public storage with no authorization keys, we can
        just simply dump out a URL rather than having to query S3 for new keys.
        """
        name = self._clean_name(name)
        if self.bucket_cname:
            return "http://%s/%s" % (self.bucket_cname, name)
        else:
            return "http://s3.amazonaws.com/%s/%s" % (self.bucket_name, name)

class S3BotoStorageFile(File):
    def __init__(self, name, mode, storage):
        self._storage = storage
        self.name = name
        self._mode = mode
        self.key = storage.bucket.get_key(name)
        self._is_dirty = False
        self.file = StringIO()

    @property
    def size(self):
        if not self.key:
            raise IOError('No such S3 key: %s' % self.name)
        return self.key.size

    def read(self, *args, **kwargs):
        self.file = StringIO()
        self._is_dirty = False
        if not self.key:
            raise IOError('No such S3 key: %s' % self.name)
        self.key.get_contents_to_file(self.file)
        return self.file.getvalue()

    def write(self, content):
        if 'w' not in self._mode:
            raise AttributeError("File was opened for read-only access.")
        self.file = StringIO(content)
        self._is_dirty = True

    def close(self):
        if self._is_dirty:
            if not self.key:
                self.key = self._storage.bucket.new_key(key_name=self.name)
            self.key.set_contents_from_string(self.file.getvalue(), headers=self._storage.headers, policy=self.storage.acl)
        self.key.close()
