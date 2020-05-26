from __future__ import absolute_import

import csv
import ntpath
import subprocess
import tempfile
import zipfile
from StringIO import StringIO
from datetime import datetime, timedelta
from tempfile import _TemporaryFileWrapper
from time import sleep
from zipfile import ZipFile

import requests
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files import File
from django.core.mail import EmailMultiAlternatives
from django.core.management import call_command
from django.utils import timezone
from django.utils.text import slugify
from django_bouncy.models import Bounce
from haystack.query import SearchQuerySet
from requests import Response

from astrobin.models import BroadcastEmail, Image, DataDownloadRequest, ImageRevision
from astrobin.utils import inactive_accounts
from astrobin_apps_images.models import ThumbnailGroup
from astrobin_apps_images.services import ImageService

logger = get_task_logger(__name__)


@shared_task()
def test_task():
    logger.info('Test task begins')
    sleep(15)
    logger.info('Test task ends')


@shared_task(rate_limit="1/s", time_limit=5)
def update_top100_ids():
    from astrobin.models import Image

    LOCK_EXPIRE = 60 * 5  # Lock expires in 5 minutes
    lock_id = 'top100_ids_lock'

    # cache.add fails if the key already exists
    acquire_lock = lambda: cache.add(lock_id, 'true', LOCK_EXPIRE)
    # memcache delete is very slow, but we have to use it to take
    # advantage of using add() for atomic locking
    release_lock = lambda: cache.delete(lock_id)

    logger.debug('Building Top100 ids...')
    if acquire_lock():
        try:
            sqs = SearchQuerySet().models(Image).order_by('-likes')
            top100_ids = [int(x.pk) for x in sqs][:100]
            cache.set('top100_ids', top100_ids, 60 * 60 * 24)
        finally:
            release_lock()
        return

    logger.debug(
        'Top100 ids task is already being run by another worker')


@shared_task()
def global_stats():
    from astrobin.models import Image, GlobalStat
    sqs = SearchQuerySet()

    users = sqs.models(User).all().count()
    images = sqs.models(Image).all().count()

    integration = 0
    for i in sqs.models(Image).all():
        integration += i.integration
    integration = int(integration / 3600.0)

    gs = GlobalStat(
        users=users,
        images=images,
        integration=integration)
    gs.save()


@shared_task()
def sync_iotd_api():
    call_command("image_of_the_day")


@shared_task()
def merge_gear():
    call_command("merge_gear")


@shared_task()
def hitcount_cleanup():
    call_command("hitcount_cleanup")


@shared_task()
def contain_imagecache_size():
    subprocess.call(['scripts/contain_directory_size.sh', '/media/imagecache', '120'])


"""
This task will delete all inactive accounts with bounced email
addresses.
"""


@shared_task()
def delete_inactive_bounced_accounts():
    bounces = Bounce.objects.filter(
        hard=True,
        bounce_type="Permanent")
    emails = bounces.values_list('address', flat=True)

    User.objects.filter(email__in=emails, is_active=False).delete()
    bounces.delete()


"""
This task gets the raw thumbnail data and sets the cache and ThumbnailGroup object.
"""


@shared_task()
def retrieve_thumbnail(pk, alias, options):
    from astrobin.models import Image

    revision_label = options.get('revision_label', 'final')

    LOCK_EXPIRE = 1
    lock_id = 'retrieve_thumbnail_%d_%s_%s' % (pk, revision_label, alias)

    acquire_lock = lambda: cache.add(lock_id, 'true', LOCK_EXPIRE)
    release_lock = lambda: cache.delete(lock_id)

    def set_thumb():
        url = thumb.url
        field = image.get_thumbnail_field(revision_label)
        if not field.name.startswith('images/'):
            field.name = 'images/' + field.name
        cache_key = image.thumbnail_cache_key(field, alias)
        cache.set(cache_key, url, 60 * 60 * 24 * 365)
        logger.debug("Image %d: saved generated thumbnail in the cache." % image.pk)
        thumbnails, created = ThumbnailGroup.objects.get_or_create(image=image, revision=revision_label)
        setattr(thumbnails, alias, url)
        thumbnails.save()
        logger.debug("Image %d: saved generated thumbnail in the database." % image.pk)
        cache.delete('%s.retrieve' % cache_key)

    if acquire_lock():
        try:
            image = Image.all_objects.get(pk=pk)
            thumb = image.thumbnail_raw(alias, options)

            if thumb:
                set_thumb()
            else:
                logger.debug("Image %d: unable to generate thumbnail." % image.pk)
        except Exception as e:
            logger.debug("Error retrieving thumbnail: %s" % e.message)
        finally:
            release_lock()
        return

    logger.debug('retrieve_thumbnail task is already running')


"""
This task retrieves all thumbnail data.
"""


@shared_task()
def retrieve_primary_thumbnails(pk, options):
    for alias in ('story', 'thumb', 'gallery', 'regular', 'hd', 'real'):
        logger.debug("Starting retrieve thumbnail for %d:%s" % (pk, alias))
        retrieve_thumbnail.delay(pk, alias, options)


@shared_task()
def update_index():
    call_command('update_index', '-k 4', '-b 100', '--remove', '--age=24')


@shared_task()
def send_missing_data_source_notifications():
    call_command("send_missing_data_source_notifications")


@shared_task()
def send_missing_remote_source_notifications():
    call_command("send_missing_remote_source_notifications")


@shared_task(rate_limit="1/s")
def send_broadcast_email(broadcastEmail, recipients):
    for recipient in list(recipients):
        msg = EmailMultiAlternatives(
            broadcastEmail.subject,
            broadcastEmail.message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient])
        msg.attach_alternative(broadcastEmail.message_html, "text/html")
        msg.send()


@shared_task()
def send_inactive_account_reminder():
    try:
        email = BroadcastEmail.objects.get(subject="We miss your astrophotographs!")
        recipients = inactive_accounts()
        send_broadcast_email.delay(email, recipients.values_list('user__email', flat=True))
        recipients.update(inactive_account_reminder_sent=timezone.now())
    except BroadcastEmail.DoesNotExist:
        pass


@shared_task()
def prepare_download_data_archive(request_id):
    # type: (str) -> None

    logger.debug("prepare_download_data_archive: called for request %d" % request_id)

    data_download_request = DataDownloadRequest.objects.get(id=request_id)

    try:
        temp_zip = tempfile.NamedTemporaryFile()  # type: _TemporaryFileWrapper
        temp_csv = StringIO()  # type: StringIO
        archive = zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED, allowZip64=True)  # type: ZipFile

        csv_writer = csv.writer(temp_csv)
        csv_writer.writerow([
            'id',
            'title',
            'acquisition_type',
            'subject_type',
            'data_source',
            'remote_source',
            'solar_system_main_subject',
            'locations',
            'description',
            'link',
            'link_to_fits',
            'image_file',
            'uncompressed_source_file',
            'uploaded', 'published',
            'updated',
            'watermark',
            'watermark_text',
            'watermark_opacity',
            'imaging_telescopes',
            'guiding_telescopes',
            'mounts',
            'imaging_cameras',
            'guiding_cameras',
            'focal_reducers',
            'software',
            'filters',
            'accessories',
            'is_wip',
            'w',
            'h',
            'animated',
            'license',
            'is_final',
            'allow_comments',
            'mouse_hover_image'
        ])

        images = Image.objects_including_wip.filter(user=data_download_request.user, corrupted=False)
        for image in images:
            id = image.get_id()  # type: str

            try:
                logger.debug("prepare_download_data_archive: image id = %s" % id)

                title = slugify(image.title)  # type: str
                path = ntpath.basename(image.image_file.name)  # type: str

                response = requests.get(image.image_file.url, verify=False)  # type: Response
                if response.status_code == 200:
                    archive.writestr("%s-%s/%s" % (id, title, path), response.content)
                    logger.debug("prepare_download_data_archive: image %s = written" % id)

                if image.solution and image.solution.image_file:
                    response = requests.get(image.solution.image_file.url, verify=False)  # type: Response
                    if response.status_code == 200:
                        path = ntpath.basename(image.solution.image_file.name)  # type: str
                        archive.writestr("%s-%s/solution/%s" % (id, title, path), response.content)
                        logger.debug("prepare_download_data_archive: solution of image %s = written" % id)

                for revision in ImageRevision.objects.filter(image=image, corrupted=False):  # type: ImageRevision
                    try:
                        label = revision.label  # type: unicode
                        path = ntpath.basename(revision.image_file.name)  # type: str

                        logger.debug("prepare_download_data_archive: image %s revision %s = iterating" % (id, label))

                        response = requests.get(revision.image_file.url, verify=False)  # type: Response
                        if response.status_code == 200:
                            archive.writestr("%s-%s/revisions/%s/%s" % (id, title, label, path), response.content)
                            logger.debug("prepare_download_data_archive: image %s revision %s = written" % (id, label))

                        if revision.solution and image.solution.image_file:
                            response = requests.get(revision.solution.image_file.url, verify=False)  # type: Response
                            if response.status_code == 200:
                                path = ntpath.basename(revision.solution.image_file.name)  # type: str
                                archive.writestr("%s-%s/revisions/%s/solution/%s" % (id, title, label, path), response.content)
                                logger.debug(
                                    "prepare_download_data_archive: solution image of image %s revision %s = written" % (
                                        id, label
                                    )
                                )
                    except Exception as e:
                        logger.exception("prepare_download_data_archive error: %s" % e.message)
                        logger.debug("prepare_download_data_archive: skipping revision %s" % label)
                        continue
            except Exception as e:
                logger.exception("prepare_download_data_archive error: %s" % e.message)
                logger.debug("prepare_download_data_archive: skipping image %s" % id)
                continue

            csv_writer.writerow([
                image.get_id(),
                unicode(image.title).encode('utf-8'),
                image.acquisition_type,
                ImageService(image).get_subject_type_label(),
                image.data_source,
                image.remote_source,
                image.solar_system_main_subject,
                ';'.join([unicode(x).encode('utf-8') for x in image.locations.all()]),
                unicode(image.description).encode('utf-8'),
                unicode(image.link).encode('utf-8'),
                unicode(image.link_to_fits).encode('utf-8'),
                image.image_file.url,
                image.uncompressed_source_file.url if image.uncompressed_source_file else "",
                image.uploaded,
                image.published,
                image.updated,
                image.watermark,
                unicode(image.watermark_text).encode('utf-8'),
                image.watermark_opacity,
                ';'.join([unicode(x).encode('utf-8') for x in image.imaging_telescopes.all()]),
                ';'.join([unicode(x).encode('utf-8') for x in image.guiding_telescopes.all()]),
                ';'.join([unicode(x).encode('utf-8') for x in image.mounts.all()]),
                ';'.join([unicode(x).encode('utf-8') for x in image.imaging_cameras.all()]),
                ';'.join([unicode(x).encode('utf-8') for x in image.guiding_cameras.all()]),
                ';'.join([unicode(x).encode('utf-8') for x in image.focal_reducers.all()]),
                ';'.join([unicode(x).encode('utf-8') for x in image.software.all()]),
                ';'.join([unicode(x).encode('utf-8') for x in image.filters.all()]),
                ';'.join([unicode(x).encode('utf-8') for x in image.accessories.all()]),
                image.is_wip,
                image.w,
                image.h,
                image.animated,
                image.license,
                image.is_final,
                image.allow_comments,
                image.mouse_hover_image
            ])

        csv_value = temp_csv.getvalue()
        archive.writestr("data.csv", csv_value)
        archive.close()

        data_download_request.status = "READY"
        data_download_request.file_size = sum([x.file_size for x in archive.infolist()])
        data_download_request.zip_file.save("", File(temp_zip))

        logger.debug("prepare_download_data_archive: completed for request %d" % request_id)
    except Exception as e:
        logger.exception("prepare_download_data_archive error: %s" % e.message)
        data_download_request.status = "ERROR"
        data_download_request.save()


@shared_task()
def expire_download_data_requests():
    DataDownloadRequest.objects \
        .exclude(status="EXPIRED") \
        .filter(created__lt=datetime.now() - timedelta(days=7)) \
        .update(status="EXPIRED")
