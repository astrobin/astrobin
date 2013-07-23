# Python
import tempfile, zipfile

# Django
from django.core.files import File

# Third party apps
from celery.task import task
import PySide.QtCore
import PyABC as abc

# This app
from .models import RawImage, TemporaryArchive

@task()
def index_raw_image(id):
    try:
        image = RawImage.objects.get(id = id)
    except RawImage.DoesNotExist:
        return

    abc_image = abc.Image()
    abc_image.load(image.file.path, image.original_filename)

    image.image_type = abc_image.type()
    image.acquisition_date = abc_image.observationDate()
    image.camera = abc_image.cameraModel()
    image.telescopeName = abc_image.telescopeName()
    image.filterName = abc_image.filterName()
    image.subjectName = abc_image.objectName()
    image.temperature = abc_image.temperature() if abc_image.hasTemperature() else None

    image.indexed = True
    image.save()


@task()
def prepare_zip(image_ids, owner_id, temp_archive_id, folder_or_pool = None):
    temp = tempfile.NamedTemporaryFile()
    archive = zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED)
    for image_id in image_ids:
        image = RawImage.objects.get(id = image_id)
        if not image.active:
            continue
        archive.write(image.file.path, image.original_filename)

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
