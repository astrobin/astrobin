from __future__ import absolute_import

import PyABC as abc
import tempfile
import zipfile

from celery import shared_task
from django.core.files import File

from .models import RawImage, TemporaryArchive


@shared_task()
def index_raw_image(id):
    try:
        image = RawImage.objects.get(id=id)
    except RawImage.DoesNotExist:
        return

    abc_image = abc.Image()
    abc_image.load(image.file.name, image.original_filename)

    image.image_type = abc_image.type()
    image.acquisition_date = abc_image.observationDate()
    image.camera = abc_image.cameraModel()
    image.telescopeName = abc_image.telescopeName()
    image.filterName = abc_image.filterName()
    image.subjectName = abc_image.objectName()
    image.temperature = abc_image.temperature() if abc_image.hasTemperature() else None

    image.indexed = True
    image.save()


@shared_task()
def prepare_zip(image_ids, owner_id, temp_archive_id, folder_or_pool = None):
    temp = tempfile.NamedTemporaryFile()
    archive = zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED)
    for image_id in image_ids:
        image = RawImage.objects.get(id = image_id)
        if not image.active:
            continue

        # Files before the migration to docker will be like '$userId/filename',
        # while files after will ne 'rawdata/files/$userId/filename'.
        path = image.file.name
        if not path.startswith('rawdata/files/'):
            path = 'rawdata/files/' + path

        try:
            remote_file = image.file.storage._open(path)
        except IOError:
            # The remote file does not exist.
            continue

        archive.writestr(image.original_filename, remote_file.read())

    archive.close()

    size = sum([x.file_size for x in archive.infolist()])

    temp_archive = TemporaryArchive.objects.get(id = temp_archive_id)
    temp_archive.size = size
    temp_archive.file.save('', File(temp))
    temp_archive.ready = True
    temp_archive.save()

    if folder_or_pool:
        folder_or_pool.archive = temp_archive
        folder_or_pool.save()
