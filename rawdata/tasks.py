# Third party apps
from celery.task import task
import PyABC as abc

# This app
from .models import RawImage

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

    image.indexed = True
    image.save()
    
