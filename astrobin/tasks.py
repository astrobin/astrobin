from django.conf import settings
from django.core.cache import cache

from celery.task import task
from celery.task.sets import subtask
from boto.exception import S3CreateError

from PIL import Image as PILImage
import subprocess

import StringIO
import os
import os.path
import signal
import time
import threading

from image_utils import *
from storage import *
from notifications import *
from storage import download_from_bucket


@task()
def solve_image(image, lang, use_scale=True, callback=None):
    # If solving is disabled in the settings, then we override what we're
    # asked to do.
    if not settings.ASTROBIN_ENABLE_SOLVING:
        return

    # Solve
    path = settings.UPLOADS_DIRECTORY
    uid = image.filename + '_resized'
    original_ext = image.original_ext
    solved = False

    def run_popen_with_timeout(command, timeout):
        """
        Run a sub-program in subprocess.Popen,
        kill it if the specified timeout has passed.
        """
        kill_check = threading.Event()
        def _kill_process_after_a_timeout(pid):
            os.kill(pid, signal.SIGKILL)
            os.system('killall -9 backend')
            kill_check.set() # tell the main routine that we had to kill
            return
        p = subprocess.Popen(command)
        pid = p.pid
        watchdog = threading.Timer(timeout, _kill_process_after_a_timeout, args=(pid, ))
        watchdog.start()
        p.communicate()
        watchdog.cancel() # if it's still waiting to run
        success = not kill_check.isSet()
        kill_check.clear()
        return success

    # If the the original image doesn't exist anymore, we need to
    # download it again.
    if not os.path.exists(path + uid + original_ext):
        print "Path doesn't exist: %s" % path + uid + original_ext
        download_from_bucket(uid + original_ext, path)

    if use_scale:
        print "Using scale."
        # Optimize for most cases
        scale_low = 0.5
        scale_high = 5
        if image.focal_length and image.pixel_size:
            scale = float(image.pixel_size) / float(image.focal_length) * 206.3
            print "Setting initial scale to %f." % scale
            # Account for the fact that we're using a resized image
            our_file = open(path + uid + original_ext)
            our_data = StringIO.StringIO(our_file.read())
            our_image = PILImage.open(our_data)
            (our_w, our_h) = our_image.size

            if image.w > 0:
                scale *= (image.w * 1./our_w)
            print "Scale changed to %f because resized image is (%f, %f) and original is (%f, %f)." % (scale, our_w, our_h, image.w, image.h)

            # Allow a 20% tolerance
            scale_low = scale * 0.95
            scale_high = scale * 1.05
            if image.binning:
                scale_low *= image.binning
                scale_high *= image.binning
            if image.scaling:
                scale_low *= 100.0 / float(image.scaling)
                scale_high *= 100.0 / float(image.scaling)
        else:
            use_scale = False

    command = ['/usr/local/astrometry/bin/solve-field',
               '', '',
               '', '',
               '', '',
               '--verbose',
               '--continue',
               path + uid + original_ext]

    if use_scale:
        command[1] = '--scale-units'
        command[2] = 'arcsecperpix'
        command[3] = '--scale-low'
        command[4] = str(scale_low)
        command[5] = '--scale-high'
        command[6] = str(scale_high)
    else:
        command[1] = '--backend-config'
        command[2] = '/usr/local/astrometry/etc/backend.blind.cfg'
        del command[3:7]

    print command
    run_popen_with_timeout(command, 330 if use_scale else 630)

    solved_filename = settings.UPLOADS_DIRECTORY + uid + '-ngc.png'
    if os.path.exists(settings.UPLOADS_DIRECTORY + uid + '.solved'):
        solved = True
        solved_file = open(solved_filename)
        solved_data = StringIO.StringIO(solved_file.read())
        solved_image = PILImage.open(solved_data)

        # Then save to bucket
        save_to_bucket(image.filename + '_solved' + original_ext, solved_data.getvalue())

    if callback is not None:
        subtask(callback).delay(image, solved, use_scale, '%s%s*' % (path, uid), lang)


@task()
def store_image(image, solve, lang, callback=None):
    try:
        (w, h, animated) = store_image_in_backend(settings.UPLOADS_DIRECTORY, image.filename, image.original_ext)
        image.w = w
        image.h = h
        image.animated = animated
    except S3CreateError, exc:
        store_image.retry(exc=exc)

    if callback is not None:
        subtask(callback).delay(image, True, solve, lang)


@task
def delete_image(filename, ext):
    delete_image_from_backend(filename, ext)

