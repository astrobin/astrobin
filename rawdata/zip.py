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
    # https://code.djangoproject.com/ticket/6027
    class FixedFileWrapper(FileWrapper):
        def __iter__(self):
            self.filelike.seek(0)
            return self

    temp = tempfile.NamedTemporaryFile()
    archive = zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED)
    for image in images:
        if not image.active:
            continue
        archive.write(image.file.path, image.original_filename)

    archive.close()

    response = None
    size = sum([x.file_size for x in archive.infolist()])
    if size < 16*1024*1024:
        wrapper = FixedFileWrapper(temp)
        response = HttpResponse(wrapper, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename=rawdata.zip'
        response['Content-Length'] = temp.tell()
        temp.seek(0)
    else:
        t = TemporaryArchive(
            user = owner,
            size = size,
        )
        t.file.save('', File(temp))
        t.save()
        response = HttpResponseRedirect(
            reverse('rawdata.temporary_archive_detail', args = (t.pk,)))

    return response
