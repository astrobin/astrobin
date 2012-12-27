# Python
import tempfile, zipfile

# Django
from django.core.files import File
from django.core.servers.basehttp import FileWrapper
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect

# This app
from .models import TemporaryArchive


def serve_zip(images, owner):
    temp = tempfile.NamedTemporaryFile()
    archive = zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED)
    for image in images:
        if not image.active:
            continue
        archive.write(image.file.path, image.original_filename)

    archive.close()

    size = sum([x.file_size for x in archive.infolist()])
    t = TemporaryArchive(
        user = owner,
        size = size,
    )
    t.file.save('', File(temp))
    t.save()
    response = HttpResponseRedirect(
        reverse('rawdata.temporary_archive_detail', args = (t.pk,)))
    return response, t
