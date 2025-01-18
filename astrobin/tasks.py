import csv
import json
import ntpath
import os
import subprocess
import tempfile
import uuid
import zipfile
from datetime import datetime, timedelta
from io import StringIO
from PIL import Image as PILImage
from time import sleep
from typing import List, Union
from xml.etree.ElementTree import Element, SubElement, tostring
from zipfile import ZipFile

import boto3
import requests
from annoying.functions import get_object_or_None
from celery import shared_task
from celery.utils.log import get_task_logger
from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.contenttypes.models import ContentType
from django.contrib.sitemaps.views import sitemap
from django.core.cache import cache
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.core.mail import EmailMultiAlternatives
from django.core.management import call_command
from django.db import IntegrityError, connections
from django.db.models import Exists, OuterRef, Q
from django.http import HttpRequest
from django.template.defaultfilters import filesizeformat
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django_bouncy.models import Bounce
from haystack.query import SearchQuerySet
from hitcount.models import HitCount
from moviepy.video.fx import resize
from moviepy.video.io.VideoFileClip import VideoFileClip
from proglog import ProgressBarLogger
from pybb.models import Post, Topic
from registration.backends.hmac.views import RegistrationView
from requests import Response

from astrobin.enums.moderator_decision import ModeratorDecision
from astrobin.models import (
    BroadcastEmail, CameraRenameProposal, DataDownloadRequest, DeepSky_Acquisition, Gear, GearMigrationStrategy,
    Image, ImageRevision, SolarSystem_Acquisition, UserProfile,
)
from astrobin.monkeypatch import _get_video_dimensions
from astrobin.services import CloudflareService
from astrobin.services.cloudfront_service import CloudFrontService
from astrobin.services.gear_service import GearService
from astrobin.services.utils_service import UtilsService
from astrobin.sitemaps.accessory_sitemap import AccessorySitemap
from astrobin.sitemaps.camera_sitemap import CameraSitemap
from astrobin.sitemaps.filter_sitemap import FilterSitemap
from astrobin.sitemaps.monthly_sitemap import generate_sitemaps
from astrobin.sitemaps.mount_sitemap import MountSitemap
from astrobin.sitemaps.software_sitemap import SoftwareSitemap
from astrobin.sitemaps.static_view_sitemap import StaticViewSitemap
from astrobin.sitemaps.telescope_sitemap import TelescopeSitemap
from astrobin.utils import inactive_accounts, never_activated_accounts, never_activated_accounts_to_be_deleted
from astrobin_apps_groups.models import Group as AstroBinGroup
from astrobin_apps_images.services import ImageService
from astrobin_apps_notifications.utils import push_notification
from astrobin_apps_users.services import UserService
from common.services import DateTimeService
from common.utils import get_segregated_reader_database
from nested_comments.models import NestedComment

logger = get_task_logger(__name__)


@shared_task(time_limit=20)
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
        'Top100 ids task is already being run by another worker'
    )


@shared_task(time_limit=60, acks_late=True)
def sync_iotd_api():
    call_command("image_of_the_day")


@shared_task(time_limit=60, acks_late=True)
def hitcount_cleanup():
    call_command("hitcount_cleanup")


@shared_task(time_limit=600, acks_late=True)
def contain_temporary_files_size():
    subprocess.call(['scripts/contain_directory_size.sh', '/astrobin-temporary-files/files', '10080'])


"""
This task will delete all inactive accounts with bounced email
addresses.
"""


@shared_task(time_limit=60, acks_late=True)
def delete_inactive_bounced_accounts():
    bounces = Bounce.objects.filter(
        hard=True,
        bounce_type="Permanent"
    )
    emails = bounces.values_list('address', flat=True)

    User.objects.filter(email__in=emails, is_active=False).delete()
    bounces.delete()


@shared_task(time_limit=300, acks_late=True)
def retrieve_thumbnail(pk, alias, revision_label, thumbnail_settings):
    from astrobin.models import Image

    LOCK_EXPIRE = 300
    lock_id = 'retrieve_thumbnail_%d_%s_%s' % (pk, revision_label, alias)

    acquire_lock = lambda: cache.add(lock_id, 'true', LOCK_EXPIRE)
    release_lock = lambda: cache.delete(lock_id)

    def drop_retrieval_cache():
        field = image.get_thumbnail_field(revision_label)
        cache_key = image.thumbnail_cache_key(field, alias, revision_label)
        cache.delete('%s.retrieve' % cache_key)

    def set_thumb():
        ImageService(image).set_thumb(alias, revision_label, thumb.url)
        drop_retrieval_cache()

    if acquire_lock():
        try:
            image = Image.all_objects.get(pk=pk)

            if not image.image_file.name:
                release_lock()
                return

            thumb = image.thumbnail_raw(alias, revision_label, thumbnail_settings=thumbnail_settings)

            if thumb:
                set_thumb()
            else:
                logger.debug("Image %d: unable to generate thumbnail." % image.pk)
                drop_retrieval_cache()
        except Exception as e:
            logger.debug("Error retrieving thumbnail: %s" % str(e))
            drop_retrieval_cache()
        finally:
            release_lock()
        return

    logger.debug('retrieve_thumbnail task is already running')


@shared_task(time_limit=3600, acks_late=True)
def generate_video_preview(object_id: int, content_type_id: int):
    LOCK_EXPIRE = 300
    lock_id = 'generate_video_preview_%d_%d' % (content_type_id, object_id)

    acquire_lock = lambda: cache.add(lock_id, 'true', LOCK_EXPIRE)
    release_lock = lambda: cache.delete(lock_id)

    if acquire_lock():
        try:
            ct = ContentType.objects.get_for_id(content_type_id)
            obj: Union[Image, ImageRevision] = ct.get_object_for_this_type(pk=object_id)

            if obj.deleted:
                logger.debug('Skip generating video preview for deleted %s' % obj)
                release_lock()
                return

            if obj.image_file.name and 'placeholder' not in obj.image_file.name:
                logger.debug('Skip generating video preview for %s because it is already generated' % obj)
                release_lock()
                return

            logger.debug('Generating video preview for %s' % obj)

            temp_file = ImageService(obj).get_local_video_file()
            temp_path = temp_file.name

            # Use _get_video_dimensions function to get the correct dimensions
            width, height = _get_video_dimensions(temp_path)

            # Generate thumbnail in the middle of the video duration
            thumbnail_path = f'/astrobin-temporary-files/files/video-thumb-{content_type_id}-{object_id}-{datetime.now().timestamp()}.jpg'
            video = VideoFileClip(temp_path)
            video.save_frame(thumbnail_path, t=video.duration / 2)
            video.close()

            # Post-process the thumbnail to adjust for correct aspect ratio
            with PILImage.open(thumbnail_path) as img:
                img = img.resize((width, height), PILImage.LANCZOS)
                img.save(thumbnail_path)

            thumbnail_file = File(open(thumbnail_path, "rb"))
            obj.image_file.save("video-thumbnail.jpg", thumbnail_file, save=False)
            obj.save(update_fields=['image_file'], keep_deleted=True)

            os.unlink(thumbnail_path)
        except Exception as e:
            logger.debug("Error generating video preview: %s" % str(e))
        finally:
            release_lock()
    else:
        logger.debug('generate_video_preview task is already running')


@shared_task(time_limit=7200, acks_late=True)
def encode_video_file(object_id: int, content_type_id: int):
    LOCK_EXPIRE = 7200
    lock_id = 'encode_video_file_%d_%d' % (content_type_id, object_id)

    acquire_lock = lambda: cache.add(lock_id, 'true', LOCK_EXPIRE)
    release_lock = lambda: cache.delete(lock_id)

    if acquire_lock():
        ct = ContentType.objects.get_for_id(content_type_id)
        obj = ct.get_object_for_this_type(pk=object_id)

        try:
            if obj.deleted:
                logger.debug('Skip encoding video file for deleted %s' % obj)
                release_lock()
                return

            if obj.encoded_video_file.name:
                logger.debug('Skip encoding video file for %s because it is already encoded' % obj)
                release_lock()
                return

            logger.debug('Encoding video file for %s' % obj)

            temp_file = ImageService(obj).get_local_video_file()
            temp_path = temp_file.name

            # Use _get_video_dimensions to get the corrected video size
            width, height = _get_video_dimensions(temp_path)
            logger.debug(f'Video size after adjustment: {width}x{height}')

            # Ensure the video dimensions are even
            if width % 2 == 1:
                width -= 1
            if height % 2 == 1:
                height -= 1

            # Resize the video if needed
            video = VideoFileClip(temp_path)
            video = video.fx(resize.resize, newsize=(width, height))

            with NamedTemporaryFile(suffix='.mp4', delete=False) as output_file:
                class ProgressLogger(ProgressBarLogger):
                    def __init__(self, content_type_id, object_id):
                        super().__init__()
                        self.last_message = ''
                        self.previous_percentage = 0
                        self.content_type_id = content_type_id
                        self.object_id = object_id

                    def callback(self, **changes):
                        # Every time the logger message is updated, this function is called with
                        # the `changes` dictionary of the form `parameter: new value`.
                        for (parameter, value) in changes.items():
                            # print ('Parameter %s is now %s' % (parameter, value))
                            self.last_message = value

                    def bars_callback(self, bar, attr, value, old_value=None):
                        if 'Writing video' in self.last_message:
                            percentage = (value / self.bars[bar]['total']) * 100
                            if 0 < percentage < 100:
                                if int(percentage) != self.previous_percentage:
                                    self.previous_percentage = int(percentage)
                                    logger.debug(self.previous_percentage)
                                    cache.set(
                                        f'video-encoding-progress-{self.content_type_id}-{self.object_id}',
                                        self.previous_percentage
                                    )

                cache.set(f'video-encoding-progress-{content_type_id}-{object_id}', 0)

                video.write_videofile(
                    output_file.name,
                    codec='libx264',
                    audio_codec='aac',
                    temp_audiofile=tempfile.mktemp(suffix='.m4a'),
                    ffmpeg_params=[
                        '-s', f'{width}x{height}',
                        '-c:v', 'libx264',
                        '-crf', '18',
                        '-pix_fmt', 'yuv420p',
                        '-map_metadata', '0',
                        '-color_primaries', 'bt709',
                        '-color_trc', 'bt709',
                        '-colorspace', 'bt709',
                        '-color_range', 'tv'
                    ],
                    logger=ProgressLogger(content_type_id, object_id)
                )

                output_file.seek(0)  # reset file pointer to the beginning
                django_file = File(output_file)

                # Close and reset database connections to avoid stale connections
                for connection in connections.all():
                    connection.close_if_unusable_or_obsolete()

                obj.encoded_video_file.save(f"encoded_{obj.uploader_name}.mp4", django_file, save=False)
                obj.save(update_fields=['encoded_video_file'], keep_deleted=True)

            video.close()

            # Note: temp_path is not removed because it might be reused by another task. It will be removed by a
            # periodic task.
            os.remove(output_file.name)

            # Mark encoding progress as complete
            cache.set(f'video-encoding-progress-{content_type_id}-{object_id}', 100)
        except Exception as e:
            cache.delete(f'video-encoding-progress-{content_type_id}-{object_id}')
            logger.debug("Error encoding video file: %s" % str(e))
            obj.encoding_error = str(e)
            obj.save(update_fields=['encoding_error'], keep_deleted=True)
        finally:
            release_lock()
    else:
        logger.debug('encode_video_file task is already running')


@shared_task(time_limit=60)
def send_missing_data_source_notifications():
    call_command("send_missing_data_source_notifications")


@shared_task(time_limit=60)
def send_missing_remote_source_notifications():
    call_command("send_missing_remote_source_notifications")


@shared_task(rate_limit="3/s", time_limit=600)
def send_broadcast_email(broadcast_email_id, recipients):
    try:
        broadcast_email = BroadcastEmail.objects.get(id=broadcast_email_id)
    except BroadcastEmail.DoesNotExist:
        logger.error("Attempted to send broadcast email that does not exist: %d" % broadcast_email_id)
        return

    for recipient in recipients:
        msg = EmailMultiAlternatives(
            broadcast_email.subject,
            broadcast_email.message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient]
        )
        msg.attach_alternative(broadcast_email.message_html, "text/html")
        msg.send()
        logger.info("Email sent to %s: %s" % (recipient.email, broadcast_email.subject))


@shared_task(time_limit=60)
def send_inactive_account_reminder():
    try:
        email = BroadcastEmail.objects.get(subject="We miss your astrophotographs!")
        recipients = inactive_accounts()
        send_broadcast_email.delay(email, list(recipients.values_list('user__email', flat=True)))
        recipients.update(inactive_account_reminder_sent=timezone.now())
    except BroadcastEmail.DoesNotExist:
        pass


@shared_task(time_limit=60)
def send_never_activated_account_reminder():
    users = never_activated_accounts()

    for user in users:
        if not hasattr(user, 'userprofile'):
            user.delete()
            continue

        push_notification(
            [user], None, 'never_activated_account', {
                'date': user.date_joined,
                'username': user.username,
                'activation_link': '%s/%s' % (
                    settings.BASE_URL,
                    reverse('registration_activate', args=(RegistrationView().get_activation_key(user),)),
                )
            }
        )

        user.userprofile.never_activated_account_reminder_sent = timezone.now()
        user.userprofile.save(keep_deleted=True)

        logger.debug("Sent 'never activated account reminder' to %d" % user.pk)


@shared_task(time_limit=300)
def delete_never_activated_accounts():
    users = never_activated_accounts_to_be_deleted()
    count = users.count()

    logger.debug("Processing %d inactive accounts..." % count)

    for user in users.iterator():
        images = Image.all_objects.using(get_segregated_reader_database()).filter(user=user).count()
        posts = Post.objects.using(get_segregated_reader_database()).filter(user=user).count()
        comments = NestedComment.objects.using(get_segregated_reader_database()).filter(author=user).count()
        if images + posts + comments == 0:
            user.delete()


@shared_task(time_limit=2700, acks_late=True)
def prepare_download_data_archive(request_id):
    # type: (str) -> None

    logger.info("prepare_download_data_archive: called for request %d" % request_id)

    data_download_request = DataDownloadRequest.objects.using(
        get_segregated_reader_database()
    ).get(
        id=request_id
    )

    try:
        temp_filename = os.path.join('/astrobin-temporary-files/files', os.urandom(12).hex())
        # Ensure the file is created
        open(temp_filename, "x").close()

        temp_zip = open(temp_filename, 'r+b')
        temp_csv = StringIO()  # type: StringIO
        archive = zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED, allowZip64=True)  # type: ZipFile

        csv_writer = csv.writer(temp_csv)
        csv_writer.writerow(
            [
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
                'uploaded',
                'published',
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
                'mouse_hover_image',
                'acquisition_details',
                'ra',
                'dec',
                'pixel_scale',
                'orientation',
                'field_radius',
            ]
        )

        images = Image.objects_including_wip.using(
            get_segregated_reader_database()
        ).filter(
            user=data_download_request.user
        )

        for image in images:
            id = image.get_id()  # type: str

            try:
                logger.debug("prepare_download_data_archive: image id = %s" % id)

                title = slugify(image.title)  # type: str
                path = ntpath.basename(image.image_file.name)  # type: str

                response = UtilsService.http_with_retries(image.image_file.url)
                if response.status_code == 200:
                    archive.writestr("%s-%s/%s" % (id, title, path), response.content)
                    logger.debug("prepare_download_data_archive: image %s = written" % id)

                if image.solution and image.solution.image_file:
                    response = UtilsService.http_with_retries(image.solution.image_file.url)
                    if response.status_code == 200:
                        path = ntpath.basename(image.solution.image_file.name)  # type: str
                        archive.writestr("%s-%s/solution/%s" % (id, title, path), response.content)
                        logger.debug("prepare_download_data_archive: solution of image %s = written" % id)

                for revision in ImageRevision.objects.using(
                    get_segregated_reader_database()
                ).filter(
                    image=image
                ):  # type: ImageRevision
                    try:
                        label = revision.label  # type: str
                        path = ntpath.basename(revision.image_file.name)  # type: str

                        logger.debug("prepare_download_data_archive: image %s revision %s = iterating" % (id, label))

                        response = UtilsService.http_with_retries(revision.image_file.url)
                        if response.status_code == 200:
                            archive.writestr("%s-%s/revisions/%s/%s" % (id, title, label, path), response.content)
                            logger.debug("prepare_download_data_archive: image %s revision %s = written" % (id, label))

                        if revision.solution and image.solution.image_file:
                            response = UtilsService.http_with_retries(revision.solution.image_file.url)
                            if response.status_code == 200:
                                path = ntpath.basename(revision.solution.image_file.name)  # type: str
                                archive.writestr(
                                    "%s-%s/revisions/%s/solution/%s" % (id, title, label, path),
                                    response.content
                                )
                                logger.debug(
                                    "prepare_download_data_archive: solution image of image %s revision %s = written" % (
                                        id, label
                                    )
                                )
                    except Exception as e:
                        logger.warning("prepare_download_data_archive error: %s" % str(e))
                        logger.debug("prepare_download_data_archive: skipping revision %s" % label)
                        continue
            except Exception as e:
                logger.warning("prepare_download_data_archive error: %s" % str(e))
                logger.debug("prepare_download_data_archive: skipping image %s" % id)
                continue

            row_data = [
                image.get_id(),
                str(image.title).encode('utf-8').decode() if image.title else '',
                image.acquisition_type,
                ImageService(image).get_subject_type_label(),
                image.data_source,
                image.remote_source,
                image.solar_system_main_subject,
                ';'.join([str(x) for x in image.locations.all()]),
                str(image.description_bbcode if image.description_bbcode else image.description).encode(
                    'utf-8'
                ).decode() if image.description_bbcode or image.description else '',
                str(image.link).encode('utf-8').decode() if image.link else '',
                str(image.link_to_fits).encode('utf-8').decode() if image.link_to_fits else '',
                image.image_file.url,
                image.uncompressed_source_file.url if image.uncompressed_source_file else '',
                image.uploaded,
                image.published if image.published else '',
                image.updated,
                image.watermark if image.watermark else '',
                str(image.watermark_text).encode('utf-8').decode() if image.watermark_text else '',
                image.watermark_opacity,
                ';'.join(
                    list(
                        set(
                            [str(x) for x in image.imaging_telescopes.all()] +
                            [str(x) for x in image.imaging_telescopes_2.all()]
                        )
                    )
                ),
                ';'.join(
                    list(
                        set(
                            [str(x) for x in image.guiding_telescopes.all()] +
                            [str(x) for x in image.guiding_telescopes_2.all()]
                        )
                    )
                ),
                ';'.join(
                    list(
                        set(
                            [str(x) for x in image.mounts.all()] +
                            [str(x) for x in image.mounts_2.all()]
                        )
                    )
                ),
                ';'.join(
                    list(
                        set(
                            [str(x) for x in image.imaging_cameras.all()] +
                            [str(x) for x in image.imaging_cameras_2.all()]
                        )
                    )
                ),
                ';'.join(
                    list(
                        set(
                            [str(x) for x in image.guiding_cameras.all()] +
                            [str(x) for x in image.guiding_cameras_2.all()]
                        )
                    )
                ),
                ';'.join(
                    [str(x) for x in image.focal_reducers.all()]
                ),
                ';'.join(
                    list(
                        set(
                            [str(x) for x in image.software.all()] +
                            [str(x) for x in image.software_2.all()]
                        )
                    )
                ),
                ';'.join(
                    list(
                        set(
                            [str(x) for x in image.filters.all()] +
                            [str(x) for x in image.filters_2.all()]
                        )
                    )
                ),
                ';'.join(
                    list(
                        set(
                            [str(x) for x in image.accessories.all()] +
                            [str(x) for x in image.accessories_2.all()]
                        )
                    )
                ),
                image.is_wip,
                image.w,
                image.h,
                image.animated,
                image.license,
                image.is_final,
                image.allow_comments,
                image.mouse_hover_image
            ]

            has_deep_sky_acquisition = DeepSky_Acquisition.objects.filter(image=image).exists()
            has_solar_system_acquisitions = SolarSystem_Acquisition.objects.filter(image=image).exists()

            if has_deep_sky_acquisition:
                row_data += [
                    '\n'.join(
                        f'{x[0]}: {x[1]}' for x in ImageService(image).get_deep_sky_acquisition_text()
                        if x is not None and x[1] is not None
                    )
                ]
            elif has_solar_system_acquisitions:
                row_data += [
                    '\n'.join(
                        f'{x[0]}: {x[1]}' for x in ImageService(image).get_solar_system_acquisition_text()
                        if x is not None and x[1] is not None
                    )
                ]

            if image.solution:
                row_data += \
                    [
                        image.solution.advanced_ra if image.solution.advanced_ra is not None else image.solution.ra,
                        image.solution.advanced_dec if image.solution.advanced_dec is not None else image.solution.dec,
                        image.solution.advanced_pixscale if image.solution.advanced_pixscale is not None else image.solution.pixscale,
                        image.solution.advanced_orientation if image.solution.advanced_orientation is not None else image.solution.orientation,
                        image.solution.radius,
                    ]

            csv_writer.writerow(row_data)

        csv_value = temp_csv.getvalue()
        archive.writestr("data.csv", csv_value)
        archive.close()

        data_download_request.status = "READY"
        data_download_request.file_size = sum([x.file_size for x in archive.infolist()])
        data_download_request.zip_file.save("", File(temp_zip))

        temp_zip.close()

        logger.info("prepare_download_data_archive: completed for request %d" % request_id)
    except Exception as e:
        logger.exception("prepare_download_data_archive error: %s" % str(e))
        data_download_request.status = "ERROR"
        data_download_request.save()


@shared_task(time_limit=60, acks_late=True)
def expire_download_data_requests():
    DataDownloadRequest.objects \
        .exclude(status="EXPIRED") \
        .filter(created__lt=datetime.now() - timedelta(days=7)) \
        .update(status="EXPIRED")


@shared_task(time_limit=60, acks_late=True)
def purge_expired_incomplete_uploads():
    deleted = Image.uploads_in_progress.filter(uploader_expires__lt=DateTimeService.now()).delete()

    if deleted is not None:
        logger.info("Purged %d expired incomplete image uploads." % deleted[0])

    deleted = ImageRevision.uploads_in_progress.filter(uploader_expires__lt=DateTimeService.now()).delete()

    if deleted is not None:
        logger.info("Purged %d expired incomplete image revision uploads." % deleted[0])


@shared_task(time_limit=60)
def perform_wise_payouts(
        wise_token, account_id, min_payout_amount, max_payout_amount, expenses_balance, expenses_buffer
):
    BASE_URL = 'https://api.transferwise.com'
    HEADERS = {'Authorization': 'Bearer %s' % wise_token}

    def get_profiles():
        result = requests.get('%s/v1/profiles' % BASE_URL, headers=HEADERS)
        result_json = result.json()

        logger.debug(result.headers)
        logger.debug(json.dumps(result_json, indent=4, sort_keys=True))
        logger.info('Wise Payout: got profiles')

        return result_json

    def get_profile_id(profiles):
        return [x for x in profiles if x['type'] == 'business' and x['details']['name'] == 'AstroBin'][0]['id']

    def get_accounts(profile_id):
        result = requests.get('%s/v1/borderless-accounts?profileId=%d' % (BASE_URL, profile_id), headers=HEADERS)
        result_json = result.json()

        logger.debug(result.headers)
        logger.debug(json.dumps(result_json, indent=4, sort_keys=True))
        logger.info('Wise Payout: got accounts')

        return result_json

    def create_quote(profile_id, currency, value):
        def get_source_amount(currency, value):
            # Always leave `expenses_buffer` in the `expenses_balance` account for expenses.
            if currency == expenses_balance:
                if value < expenses_buffer:
                    # Skip to the next balance.
                    return 0
                result = value - expenses_buffer
            else:
                result = value
            return result

        source_amount = get_source_amount(currency, value)

        if source_amount < min_payout_amount:
            logger.info('Wise Payout: amount is %d < %d, bailing.' % (source_amount, min_payout_amount))
            return None

        result = requests.post(
            '%s/v2/quotes' % BASE_URL, json={
                'profile': profile_id,
                'sourceCurrency': currency,
                'sourceAmount': min(max_payout_amount, source_amount),
                'targetCurrency': 'CHF',
            }, headers=HEADERS
        )
        result_json = result.json()

        logger.debug(result.headers)
        logger.debug(json.dumps(result_json, indent=4, sort_keys=True))

        if 'errors' not in result_json:
            logger.info('Wise Payout: created quote %s' % result_json['id'])
            return result_json

        for error in result_json['errors']:
            logger.error("Wise Payout: error %s" % error['message'])

        return None

    def create_transfer(account_id, quote_id, transactionId=None):
        result = requests.post(
            '%s/v1/transfers' % BASE_URL, json={
                'targetAccount': account_id,
                'quoteUuid': quote_id,
                'customerTransactionId': transactionId if transactionId else str(uuid.uuid4())
            }, headers=HEADERS
        )
        result_json = result.json()

        logger.debug(result.headers)
        logger.debug(json.dumps(result_json, indent=4, sort_keys=True))

        if 'errors' not in result_json:
            logger.info('Wise Payout: created transfer %d' % result_json['id'])
            return result_json

        for error in result_json['errors']:
            logger.error("Wise Payout: error %s" % error['message'])

        return None

    def create_fund(profile_id, transfer_id):
        result = requests.post(
            '%s/v3/profiles/%d/transfers/%d/payments' % (BASE_URL, profile_id, transfer_id),
            json={
                'type': 'BALANCE'
            }, headers=HEADERS
        )
        result_json = result.json()

        logger.debug(result.headers)
        logger.debug(json.dumps(result_json, indent=4, sort_keys=True))
        logger.info('Wise Payout: created fund %d' % result_json['balanceTransactionId'])

        return result_json

    def process_wise_payouts():
        profiles = get_profiles()
        profile_id = get_profile_id(profiles)

        logger.info('Wise Payout: beginning for profile %d' % profile_id)

        accounts = get_accounts(profile_id)

        for account in accounts:
            logger.info('Wise Payout: processing account %d' % account['id'])

            for balance in account['balances']:
                balance_id = balance['id']
                currency = balance['currency']
                value = balance['amount']['value']

                logger.info('Wise Payout: processing balance (%d, %s, %.2f)' % (balance_id, currency, value))

                quote = create_quote(profile_id, currency, value)

                if quote is None:
                    logger.warning("Wise Payout: unable to create quote")
                    continue

                transfer = create_transfer(account_id, quote['id'])

                if transfer is None:
                    logger.warning("Wise Payout: unable to create transfer")
                    continue

                fund = create_fund(profile_id, transfer['id'])

                if fund is None:
                    logger.warning("Wise Payout: unable to create fund")
                    continue

                logger.info('Wise Payout: done processing balance (%d, %s, %.2f)' % (balance_id, currency, value))

    process_wise_payouts()


@shared_task(time_limit=300, acks_late=True)
def assign_upload_length():
    """
    Run this tasks every hour to assign `uploader_upload_length` to images that lack it.
    """

    def process(items):
        for item in items.iterator():
            try:
                url = item.image_file.url
                response = requests.head(url)  # type: Response
            except ValueError as e:
                logger.error("assign_upload_length: error %s", str(e))
                continue

            if response.status_code == 200:
                size = response.headers.get("Content-Length")
                item.uploader_upload_length = size

                try:
                    item.save(keep_deleted=True)
                except IntegrityError:
                    continue

                logger.info(
                    "assign_upload_length: proccessed %d (%s) = %s" % (
                        item.pk, item.image_file.url, filesizeformat(size)
                    )
                )

    time_cut = DateTimeService.now() - timedelta(hours=2)
    images = Image.all_objects.filter(uploader_upload_length__isnull=True, uploaded__gte=time_cut)
    revisions = ImageRevision.all_objects.filter(uploader_upload_length__isnull=True, uploaded__gte=time_cut)

    process(images)
    process(revisions)


@shared_task(time_limit=30)
def clear_duplicate_hit_counts():
    duplicates = HitCount.objects.exclude(
        pk=OuterRef('pk')
    ).filter(
        content_type_id=OuterRef('content_type_id'),
        object_pk=OuterRef('object_pk')
    )

    HitCount.objects.annotate(
        has_other=Exists(duplicates)
    ).filter(
        has_other=True
    ).delete()


@shared_task(time_limit=30)
def expire_gear_migration_locks():
    cutoff = timezone.now() - timedelta(hours=1)

    Gear.objects.filter(
        migration_flag_moderator_lock__isnull=False,
        migration_flag_moderator_lock_timestamp__lt=cutoff
    ).update(
        migration_flag_moderator_lock=None,
        migration_flag_moderator_lock_timestamp=None
    )

    GearMigrationStrategy.objects.filter(
        migration_flag_reviewer_lock__isnull=False,
        migration_flag_reviewer_lock_timestamp__lt=cutoff
    ).update(
        migration_flag_reviewer_lock=None,
        migration_flag_reviewer_lock_timestamp=None
    )


@shared_task(time_limit=600, acks_late=True)
def process_camera_rename_proposal(gear_rename_proposal_pk: int):
    proposal = CameraRenameProposal.objects.get(pk=gear_rename_proposal_pk)
    GearService.process_camera_rename_proposal(proposal)


@shared_task(time_limit=600, acks_late=True)
def update_index(content_type_pk, object_pk):
    signal_processor = apps.get_app_config('haystack').signal_processor

    if not hasattr(signal_processor, 'enqueue_save'):
        return

    content_type = ContentType.objects.get(pk=content_type_pk)
    model_class = content_type.model_class()

    try:
        instance = model_class.objects.get(pk=object_pk)
    except model_class.DoesNotExist:
        # The object was deleted before the task was executed.
        return

    signal_processor.enqueue_save(model_class, instance)


@shared_task(time_limit=3600, acks_late=False)
def hard_delete_deleted_users():
    profiles = UserProfile.deleted_objects.filter(
        deleted__lt=DateTimeService.now() - timedelta(days=365)
    )

    for profile in profiles.iterator():
        logger.info("hard_delete_deleted_users: deleting %d" % profile.user.id)
        try:
            profile.user.delete()
        except Exception as e:
            logger.error("hard_delete_deleted_users: error %s" % str(e))
            continue


@shared_task(
    time_limit=60,
    acks_late=False,
    rate_limit="6/m",
)
def invalidate_cdn_caches(paths: List[str]):
    logger.debug(f'Invalidating CDN caches for {", ".join(paths)}')
    CloudFrontService(settings.CLOUDFRONT_CDN_DISTRIBUTION_ID).create_invalidation(paths)
    CloudflareService().purge_cache(paths)


@shared_task(time_limit=3600, acks_late=True)
def generate_sitemaps_and_upload_to_s3():
    return

    invalidate_urls = []

    def upload_to_sitemap_folder(filename, folder='sitemaps'):
        # Use boto3 to upload the file to S3
        s3_client = boto3.client('s3')
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        s3_path = f'{folder}/{filename}'
        tmp_dir = tempfile.gettempdir()
        filepath = f'{tmp_dir}/{filename}'

        with open(filepath, 'rb') as file:
            s3_client.upload_fileobj(
                file,
                bucket_name,
                s3_path,
                ExtraArgs={
                    'CacheControl': 'max-age=2592000',  # 30 days
                    'ContentType': 'application/xml',
                },
            )
            logger.debug(f'Uploaded to s3: {s3_path}')

        os.remove(filepath)
        invalidate_urls.append(f'/{s3_path}')

    def generate_sitemap_index(sitemaps, base_url=settings.AWS_STORAGE_BUCKET_NAME, folder='sitemaps'):
        root = Element('sitemapindex', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
        for s in sitemaps:
            sitemap_elem = SubElement(root, 'sitemap')
            loc = SubElement(sitemap_elem, 'loc')
            loc.text = f'https://{base_url}/{folder}/{s}'

        return tostring(root, encoding='utf-8', method='xml')

    www_sitemaps = {
        'folder': 'sitemaps/www',
        'sitemaps': {
            'static': StaticViewSitemap,
            **generate_sitemaps(
                Image.objects.using(
                    get_segregated_reader_database()
                ).filter(
                    moderator_decision=ModeratorDecision.APPROVED
                ).order_by(
                    '-published'
                ),
                'published'
            ),
            **generate_sitemaps(
                UserProfile.objects.using(
                    get_segregated_reader_database()
                ).filter(
                    updated__isnull=False
                ).order_by(
                    '-updated'
                ),
                'updated'
            ),
            **generate_sitemaps(
                Topic.objects.using(
                    get_segregated_reader_database()
                ).filter(
                    Q(on_moderation=False) &
                    Q(
                        Q(forum__group=None) | Q(forum__group__public=True)
                    )
                ).order_by(
                    '-updated'
                ),
                'updated'
            ),
            **generate_sitemaps(
                AstroBinGroup.objects.using(
                    get_segregated_reader_database()
                ).filter(
                    public=True
                ).order_by(
                    '-date_updated'
                ),
                'date_updated'
            ),
        }
    }

    app_sitemaps = {
        'folder': 'sitemaps/app',
        'sitemaps': {
            'cameras': CameraSitemap,
            'telescopes': TelescopeSitemap,
            'mounts': MountSitemap,
            'filters': FilterSitemap,
            'accessories': AccessorySitemap,
            'software': SoftwareSitemap,
        }
    }

    # Create a fake request object
    request = HttpRequest()
    request.user = AnonymousUser()
    request.META['SERVER_NAME'] = settings.BASE_URL
    request.META['SERVER_PORT'] = '443'

    for custom_sitemap in (www_sitemaps, app_sitemaps):
        all_filenames = []
        tmp_dir = tempfile.gettempdir()

        # Generate and save sitemap files
        for section, site in custom_sitemap['sitemaps'].items():
            filename = f'{section}.xml'
            filepath = f'{tmp_dir}/{filename}'

            logger.debug(f'Generating sitemap {filename}')
            response = sitemap(request, custom_sitemap['sitemaps'], section)
            response.render()

            with open(filepath, 'wb') as file:
                file.write(response.content)
            upload_to_sitemap_folder(filename, folder=custom_sitemap['folder'])

            all_filenames.append(filename)

        # Generate and save sitemap index file
        sitemap_index = generate_sitemap_index(all_filenames, folder=custom_sitemap['folder'])

        # Save and upload the sitemap index
        with open(f'{tmp_dir}/sitemap_index.xml', 'wb') as file:
            file.write(sitemap_index)
        upload_to_sitemap_folder('sitemap_index.xml', folder=custom_sitemap['folder'])

        CloudFrontService(settings.CLOUDFRONT_CDN_DISTRIBUTION_ID).create_invalidation(invalidate_urls)


@shared_task(time_limit=60)
def compute_contribution_index(user_id: int):
    user = get_object_or_None(User, pk=user_id)
    if user:
        index = UserService(user).compute_contribution_index()
        UserProfile.objects.filter(user=user).update(contribution_index=index)


@shared_task(time_limit=60)
def compute_image_index(user_id: int):
    user = get_object_or_None(User, pk=user_id)
    if user:
        index = UserService(user).compute_image_index()
        UserProfile.objects.filter(user=user).update(image_index=index)


@shared_task(time_limit=120)
def invalidate_all_image_thumbnails(pk: int):
    image = get_object_or_None(Image.all_objects, pk=pk)
    if image:
        ImageService(image).invalidate_all_thumbnails()


@shared_task(time_limit=600)
def remove_deleted_images_from_search_index(time_limit: str):
    call_command("remove_deleted_images_from_search_index", time_limit=time_limit)
