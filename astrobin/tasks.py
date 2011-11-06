from django.conf import settings
from django.core.cache import cache

from celery.decorators import task
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

SUBPROCESS_EXPIRE = 60 * 5

@task()
def solve_image(image, callback=None):
	# If solving is disabled in the settings, then we override what we're
	# asked to do.
	if not settings.ASTROBIN_ENABLE_SOLVING:
		return

	# Solve
	path = settings.UPLOADS_DIRECTORY
	uid = image.filename
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

	command = ['/usr/local/astrometry/bin/solve-field', path + uid + original_ext]
	run_popen_with_timeout(command, SUBPROCESS_EXPIRE)

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

	if callback is not None:
		subtask(callback).delay(image, solved, '%s%s*' % (path, uid))


@task()
def store_image(image, solve, callback=None):
    try:
        store_image_in_backend(settings.UPLOADS_DIRECTORY, image.filename, image.original_ext)
    except S3CreateError, exc:
        store_image.retry(exc=exc)

    if callback is not None:
        subtask(callback).delay(image, True, solve)


@task
def delete_image(filename, ext):
    delete_image_from_backend(filename, ext)

