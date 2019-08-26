# Python
import datetime

# Django
from django.core.urlresolvers import reverse

# AstroBin
from astrobin.models import Image, ImageRevision


def test_utils_get_last_image():
    return Image.objects_including_wip.all().order_by('-id')[0]


def test_utils_get_last_image_revision():
    return ImageRevision.objects.all().order_by('-id')[0]


def test_utils_upload_image(test, filename = 'astrobin/fixtures/test.jpg', wip = False):
    data = {'image_file': open(filename, 'rb')}
    if wip:
        data['wip'] = True

    response = test.client.post(
        reverse('image_upload_process'),
        data,
        follow = True)
    image = test_utils_get_last_image()

    return response, image


def test_utils_upload_revision(test, image, filename = 'astrobin/fixtures/test.jpg'):
    response = test.client.post(
        reverse('image_revision_upload_process'),
        {'image_id': image.get_id(), 'image_file': open(filename, 'rb')},
        follow = True)
    revision = test_utils_get_last_image_revision()

    return response, revision


def test_utils_approve_image(image):
    image.moderator_decision = 1
    image.moderated_when = datetime.date.today()
    image.save(keep_deleted=True)
