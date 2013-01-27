# Django
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

# This app
from .models import TemporaryArchive
from .tasks import prepare_zip

def serve_zip(images, owner, folder_or_pool = None):
    archive = TemporaryArchive(user = owner)
    archive.save()

    image_ids = images.values_list('id', flat = True)
    prepare_zip.delay(image_ids, owner.id, archive.id, folder_or_pool)

    response = HttpResponseRedirect(
        reverse('rawdata.temporary_archive_detail', args = (archive.pk,)))
    return response
