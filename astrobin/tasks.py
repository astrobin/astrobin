from django.conf import settings
from django.core.cache import cache

from celery.task import task
from celery.task.sets import subtask
from boto.exception import S3CreateError

from PIL import Image as PILImage
import subprocess
from subprocess import PIPE

import StringIO
import os
import os.path
import signal
import time
import threading
import simplejson
import glob

from image_utils import *
from storage import *
from notifications import *
from storage import download_from_bucket

@task()
def image_solved_callback(image, solved, subjects, did_use_scale, clean_path, lang):
    if solved:
        print "Image was solved."
    else:
        print "Solving failed."
        if did_use_scale:
            # Try again!
            print "Trying again."
            solve_image.delay(image, lang, False, callback=image_solved_callback)
            return

    image.is_solved = solved
    if image.__class__.__name__ == 'Image' and image.is_solved:
        # grab objects from json
        import simbad
        subjects = simplejson.loads(subjects)
        if subjects['annotations']:
            print "Subjects found"
            for i in subjects['annotations']:
                print "Searching for %s..." % i['names'][0]
                s = simbad.find_single_subject(i['names'][0])
                if s:
                    image.subjects.add(s)
                    print "%s added." % s.mainId
        else:
            print "No subjects found."

    image.plot_is_overlay = image.is_solved
    image.save()

    user = None
    img = None
    try:
        user = image.user
        img = image
    except AttributeError:
        # It's a revision
        user = image.image.user
        img = image.image

    translation.activate(lang)
    if solved:
        push_notification([user], 'image_solved',
                          {'object_url':'%s%s%s' % (settings.ASTROBIN_BASE_URL, img.get_absolute_url(), '?mod=solved')})
    else:
        push_notification([user], 'image_not_solved',
                          {'object_url':'%s%s' % (settings.ASTROBIN_BASE_URL, img.get_absolute_url())})

    # Clean up!
    clean_list = glob.glob(clean_path)
    for f in clean_list:
        os.remove(f)


@task()
def image_stored_callback(image, stored, solve, lang):
    image.is_stored = stored
    image.save()

    user = None
    img = None
    is_revision = False
    try:
        user = image.user
        img = image
    except AttributeError:
        # It's a revision
        is_revision = True
        user = image.image.user
        img = image.image

    from models import UserProfile, Gear
    translation.activate(lang)
    push_notification([user], 'image_ready', {'object_url':'%s%s' %(settings.ASTROBIN_BASE_URL, img.get_absolute_url())})

    if not img.is_wip:
        followers = [x.from_userprofile.user
                     for x in UserProfile.follows.through.objects.filter(to_userprofile=user)]
        notification = 'new_image_revision' if is_revision else 'new_image'
        push_notification(followers, notification,
                          {'originator':user,
                           'object_url':settings.ASTROBIN_BASE_URL + image.get_absolute_url()
                          }
                         )
        for gear_type in ('imaging_telescopes', 'guiding_telescopes', 'mounts',
                          'imaging_cameras', 'guiding_cameras', 'focal_reducers',
                          'software', 'filters', 'accessories'):
            for gear_item in getattr(image, gear_type).all():
                gear_followers = [x.user for x in UserProfile.objects.filter(follows_gear = Gear.objects.get(id = gear_item.id))]
                push_notification(
                    gear_followers, 'new_image_from_gear',
                    {
                        'gear': gear_item.name,
                        'object_url': settings.ASTROBIN_BASE_URL + image.get_absolute_url()
                    })


    if solve:
        solve_image.delay(image, lang, callback=image_solved_callback)


@task()
def solve_image(image, lang, use_scale=True, callback=None):
    # If solving is disabled in the settings, then we override what we're
    # asked to do.
    if not settings.ASTROBIN_ENABLE_SOLVING:
        return

    if image.presolve_information < 2:
        print "Not solving, as requested."
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
        print "Runnind command: %s" % ' '.join(command)
        p = subprocess.Popen(command, bufsize=1, shell=False,
                             stdout=PIPE, stderr=PIPE)
        pid = p.pid
        watchdog = threading.Timer(timeout, _kill_process_after_a_timeout, args=(pid, ))
        watchdog.start()
        (stdout, stderr) = p.communicate()
        watchdog.cancel() # if it's still waiting to run
        success = not kill_check.isSet()
        kill_check.clear()
        return (success, stdout, stderr)

    # If the the original image doesn't exist anymore, we need to
    # download it again.
    if not os.path.exists(path + uid + original_ext):
        print "Path doesn't exist: %s" % path + uid + original_ext
        download_from_bucket(uid + original_ext, path)

    our_file = open(path + uid + original_ext)
    our_data = StringIO.StringIO(our_file.read())
    our_image = PILImage.open(our_data)
    (our_w, our_h) = our_image.size

    if use_scale:
        print "Using scale."
        # Optimize for most cases
        scale_low = 0.1
        scale_high = 180
        if image.presolve_information == 3:
            scale_low = 10
            scale_high = 180
        elif image.presolve_information == 4:
            scale_low = 0.9
            scale_high = 10
        elif image.presolve_information == 5:
            scale_low = 0.1
            scale_high = 1.1
        else:
            use_scale = False

    command = ['/usr/local/astrometry/bin/solve-field',
               '', '',
               '', '',
               '', '',
               '--objs', '100',
               '--continue',
               '--no-plot',
               path + uid + original_ext]

    if use_scale:
        command[1] = '--scale-units'
        command[2] = 'degwidth'
        command[3] = '--scale-low'
        command[4] = str(scale_low)
        command[5] = '--scale-high'
        command[6] = str(scale_high)
    else:
        command[1] = '--backend-config'
        command[2] = '/usr/local/astrometry/etc/backend.blind.cfg'
        del command[3:7]

    (success, stdout, stderr) = run_popen_with_timeout(command, 630)
    print stdout

    subjects = ''
    if os.path.exists(settings.UPLOADS_DIRECTORY + uid + '.solved'):
        # Now let's plot
        solved_filename = path + uid + '-ngc.png'
        command = [
            '/usr/local/astrometry/bin/plot-constellations',
            '-w', path + uid + '.wcs', # input
            '-o', solved_filename, # output
            '-f', '8', # font size
            '-n', '1', # line width
            '-N', # plot NGC objects
            '-C', # plot constellations
            '-B', # plot named bright stars
            '-c', # only plot bright stars that have common names
            '-j', # if a bright star has a common name, only print that
            '-J', # print JSON output to stderr
        ]
        (success, stdout, subjects) = run_popen_with_timeout(command, 60) # should't really take long
        print subjects

        print solved_filename
        if os.path.exists(solved_filename):
            print "Solved."
            solved = True
            solved_file = open(solved_filename)
            solved_data = StringIO.StringIO(solved_file.read())
            solved_image = PILImage.open(solved_data)

            # Then save to bucket
            save_to_bucket(image.filename + '_solved.png', solved_data.getvalue())

            # Now let's get some data
            command = [
                '/usr/local/astrometry/bin/wcsinfo',
                path + uid + '.wcs'
            ]
            (success, info, stderr) = run_popen_with_timeout(command, 5)
            for line in info.split('\n'):
                try:
                    key, value = line.split(' ')
                except ValueError:
                    continue
                if key in ('ra_center_hms', 'dec_center_dms', 'pixscale', 'orientation', 'fieldw', 'fieldh', 'fieldunits'):
                    print key, value
                    if key == 'pixscale':
                        value = float(value)
                        if image.w > 0 and image.w != our_w:
                            value *= our_w / float(image.w)
                        else:
                            value = 0

                    setattr(image, key, value)
            image.save()

    if callback is not None:
        print "Calling solved callback."
        subtask(callback).delay(image, solved, subjects, use_scale, '%s%s*' % (path, uid), lang)


@task()
def store_image(image, solve, lang, callback=None):
    try:
        (w, h, animated) = store_image_in_backend(settings.UPLOADS_DIRECTORY, image)
        image.w = w
        image.h = h
        image.animated = animated
        image.save()
    except S3CreateError, exc:
        store_image.retry(exc=exc)

    if callback is not None:
        subtask(callback).delay(image, True, solve, lang)


@task()
def delete_image(filename, ext):
    delete_image_from_backend(filename, ext)

