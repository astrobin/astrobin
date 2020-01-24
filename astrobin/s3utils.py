# Python
import hashlib
import logging
import os
from unidecode import unidecode

# Django
from django.conf import settings
from django.contrib.staticfiles.storage import ManifestFilesMixin
from django.core.files.storage import FileSystemStorage

# Third party
from storages.backends.s3boto import S3BotoStorage
from pipeline.storage import PipelineMixin


log = logging.getLogger('apps')


class OverwritingFileSystemStorage(FileSystemStorage):
    def get_available_name(self, name, max_length=None):
        """
        Returns the only possible filename, not caring if the file gets overwritten.
        """
        dir_name, file_name = os.path.split(name)
        file_root, file_ext = os.path.splitext(file_name)
        name = os.path.join(dir_name, "%s%s" % (file_root, file_ext))

        return name

    def generate_local_name(self, name):
        return name

    def _save(self, name, content):
        """
        We're going to delete the file before we save it.
        """
        full_path = self.path(name)

        try:
            os.remove(full_path)
        except OSError:
            pass

        return super(OverwritingFileSystemStorage, self)._save(name, content)


class CachedS3BotoStorage(S3BotoStorage):
    def __init__(self, *args, **kwargs):
        super(CachedS3BotoStorage, self).__init__()
        self.local_storage = OverwritingFileSystemStorage(location = settings.IMAGE_CACHE_DIRECTORY)

    def generate_local_name(self, name):
        local_name = hashlib.md5(unidecode(name)).hexdigest()
        log.debug("Generated localname: %s -> %s" % (name, local_name))
        return local_name

    def _save(self, name, content):
        name = super(CachedS3BotoStorage, self)._save(name, content)

        try:
            local_name = self.generate_local_name(name)
            self.local_storage._save(local_name, content)
        except (OSError, UnicodeEncodeError) as e:
            # Probably the filename was too long for the local storage.
            pass

        return name

if settings.AWS_S3_ENABLED:
    ImageStorage = lambda: CachedS3BotoStorage()
else:
    ImageStorage = lambda: OverwritingFileSystemStorage(location=settings.UPLOADS_DIRECTORY)


class S3PipelineStorage(PipelineMixin, ManifestFilesMixin, S3BotoStorage):
    pass
StaticRootS3BotoStorage = lambda: S3PipelineStorage(location=settings.STATIC_ROOT)

class LocalPipelineStorage(PipelineMixin, ManifestFilesMixin, FileSystemStorage):
    pass
StaticRootLocalStorage = lambda: LocalPipelineStorage(
    location=settings.STATIC_ROOT,
    base_url=settings.STATIC_ROOT)
