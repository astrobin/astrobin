from django.conf import settings
from celery.decorators import task
from celery.task.sets import subtask

from PIL import Image as PILImage
from subprocess import call

import StringIO
import os
import os.path

from image_utils import *
from s3 import *
from notifications import *

@task()
def solve_image(image, callback=None):
    # Solve
    path = settings.UPLOADS_DIRECTORY
    uid = image.filename
    original_ext = image.original_ext
    solved = False

    command = ['nice', '-n', '5', '/usr/local/astrometry/bin/solve-field', path + uid + original_ext]
    call(command)
    solved_filename = settings.UPLOADS_DIRECTORY + image.filename + '-ngc.png'
    if os.path.exists(settings.UPLOADS_DIRECTORY + image.filename + '.solved'):
        solved = True
        solved_file = open(solved_filename)
        solved_data = StringIO.StringIO(solved_file.read())
        solved_image = PILImage.open(solved_data)

        (w, h) = solved_image.size
        (w, h) = scale_dimensions(w, h, settings.RESIZED_IMAGE_SIZE)
        solved_resizedImage = solved_image.resize((w, h), PILImage.ANTIALIAS)

        # Then save to bucket
        solved_resizedFile = StringIO.StringIO()
        solved_resizedImage.save(solved_resizedFile, 'PNG')
        save_to_bucket(uid + '_solved.png', solved_resizedFile.getvalue())
    if solved:
        push_notification([image.user], 'image_solved',
                          {'object_url':image.get_absolute_url() + '?mod=solved'})
    else:
        push_notification([image.user], 'image_not_solved',
                          {'object_url':image.get_absolute_url()})

    if callback:
        callback(image, solved, '%s%s*' % (path, uid))


@task()
def store_image(image, solve, callback=None):
    try:
        store_image_in_s3(settings.UPLOADS_DIRECTORY, image.filename, image.original_ext)
    except S3CreateError, exc:
        store_image.retry(exc=exc)

    push_notification([image.user], 'image_ready', {'object_url':image.get_absolute_url()})

    if callback:
        callback(image, True, solve)


@task
def delete_image(filename, ext):
    delete_image_from_s3(filename, ext)


