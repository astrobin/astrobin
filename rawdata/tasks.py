from celery.task import task

from .models import RawImage

@task()
def index_raw_image(id):
    def generate_dummy_data():
        from random import choice
        image_type = choice(('0', '10', '20', '30', '40',))

        return {
            'image_type': image_type,
        }

    try:
        image = RawImage.objects.get(id = id)
    except RawImage.DoesNotExist:
        return

    data = generate_dummy_data()
    image.image_type = data['image_type']
    image.indexed = True
    image.save()
    
