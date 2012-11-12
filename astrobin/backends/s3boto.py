from django.core.files.storage import get_storage_class
from django.utils.functional import SimpleLazyObject

from storages.backends.s3boto import S3BotoStorage

class CachedStorage(S3BotoStorage):
    """S3 storage backend that saves the files locally, too.
    """
    def __init__(self, *args, **kwargs):
        super(CachedStorage, self).__init__(*args, **kwargs)
        self.local_storage = get_storage_class(
            "compressor.storage.CompressorFileStorage")()

    def save(self, name, content):
        name = super(CachedStorage, self).save(name, content)
        self.local_storage._save(name, content)
        return name

StaticStorage = lambda: CachedStorage(location='www/static')
DefaultStorage  = lambda: CachedStorage()
