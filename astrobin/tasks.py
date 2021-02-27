from __future__ import absolute_import

import json
import uuid

import six

import csv
import ntpath
import subprocess
import tempfile
import zipfile

from common.services import DateTimeService

if six.PY2:
    from StringIO import StringIO
else:
    from io import StringIO
from datetime import datetime, timedelta
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
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django_bouncy.models import Bounce
from haystack.query import SearchQuerySet
from registration.backends.hmac.views import RegistrationView
from requests import Response

from astrobin.models import BroadcastEmail, Image, DataDownloadRequest, ImageRevision
from astrobin.utils import inactive_accounts, never_activated_accounts, never_activated_accounts_to_be_deleted
from astrobin_apps_images.services import ImageService
from astrobin_apps_notifications.utils import push_notification

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
        'Top100 ids task is already being run by another worker')


@shared_task(time_limit=60)
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


@shared_task(time_limit=60)
def sync_iotd_api():
    call_command("image_of_the_day")


@shared_task(time_limit=60)
def merge_gear():
    call_command("merge_gear")


@shared_task(time_limit=60)
def hitcount_cleanup():
    call_command("hitcount_cleanup")


@shared_task(time_limit=60)
def contain_temporary_files_size():
    subprocess.call(['scripts/contain_directory_size.sh', '/astrobin-temporary-files/files', '120'])


"""
This task will delete all inactive accounts with bounced email
addresses.
"""


@shared_task(time_limit=60)
def delete_inactive_bounced_accounts():
    bounces = Bounce.objects.filter(
        hard=True,
        bounce_type="Permanent")
    emails = bounces.values_list('address', flat=True)

    User.objects.filter(email__in=emails, is_active=False).delete()
    bounces.delete()


@shared_task(time_limit=120)
def retrieve_thumbnail(pk, alias, revision_label, thumbnail_settings):
    from astrobin.models import Image

    LOCK_EXPIRE = 1
    lock_id = 'retrieve_thumbnail_%d_%s_%s' % (pk, revision_label, alias)

    acquire_lock = lambda: cache.add(lock_id, 'true', LOCK_EXPIRE)
    release_lock = lambda: cache.delete(lock_id)

    def set_thumb():
        field = image.get_thumbnail_field(revision_label)
        cache_key = image.thumbnail_cache_key(field, alias)

        ImageService(image).set_thumb(alias, revision_label, thumb.url)

        cache.delete('%s.retrieve' % cache_key)

    if acquire_lock():
        try:
            image = Image.all_objects.get(pk=pk)
            thumb = image.thumbnail_raw(alias, revision_label, thumbnail_settings=thumbnail_settings)

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


@shared_task(time_limit=600)
def update_index(model, age_in_minutes, batch_size):
    start = datetime.now() - timedelta(minutes=age_in_minutes)
    end = datetime.now()

    call_command(
        'update_index',
        model,
        '-b %d'  % batch_size,
        '--start=%s' % start.strftime("%Y-%m-%dT%H:%M:%S"),
        '--end=%s' % end.strftime("%Y-%m-%dT%H:%M:%S")
    )


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
            [recipient])
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

        push_notification([user], 'never_activated_account', {
            'date': user.date_joined,
            'username': user.username,
            'activation_link': '%s/%s' % (
                settings.BASE_URL,
                reverse('registration_activate', args=(RegistrationView().get_activation_key(user),)),
            )
        })

        user.userprofile.never_activated_account_reminder_sent = timezone.now()
        user.userprofile.save()

        logger.debug("Sent 'never activated account reminder' to %d" % user.pk)


@shared_task(time_limit=60)
def delete_never_activated_accounts():
    users = never_activated_accounts_to_be_deleted()
    count = users.count()
    users.delete()
    logger.debug("Deleted %d inactive accounts" % count)


@shared_task(time_limit=600)
def prepare_download_data_archive(request_id):
    # type: (str) -> None

    logger.info("prepare_download_data_archive: called for request %d" % request_id)

    data_download_request = DataDownloadRequest.objects.get(id=request_id)

    try:
        temp_zip = tempfile.NamedTemporaryFile()
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
                        logger.warning("prepare_download_data_archive error: %s" % e.message)
                        logger.debug("prepare_download_data_archive: skipping revision %s" % label)
                        continue
            except Exception as e:
                logger.warning("prepare_download_data_archive error: %s" % e.message)
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

        logger.info("prepare_download_data_archive: completed for request %d" % request_id)
    except Exception as e:
        logger.exception("prepare_download_data_archive error: %s" % e.message)
        data_download_request.status = "ERROR"
        data_download_request.save()


@shared_task(time_limit=60)
def expire_download_data_requests():
    DataDownloadRequest.objects \
        .exclude(status="EXPIRED") \
        .filter(created__lt=datetime.now() - timedelta(days=7)) \
        .update(status="EXPIRED")


@shared_task(time_limit=60)
def purge_expired_incomplete_uploads():
    deleted, _ = Image.uploads_in_progress.filter(uploader_expires__lt=DateTimeService.now()).delete()
    logger.info("Purged %d expired incomplete image uploads." % deleted)

    deleted, _ = ImageRevision.uploads_in_progress.filter(uploader_expires__lt=DateTimeService.now()).delete()
    logger.info("Purged %d expired incomplete image revision uploads." % deleted)


@shared_task(time_limit=60)
def perform_wise_payouts(
        wise_token, account_id, min_payout_amount, max_payout_amount, expenses_balance, expenses_buffer):
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
        return [x for x in profiles if x['type'] == u'business' and x['details']['name'] == u'AstroBin'][0]['id']

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

        result = requests.post('%s/v2/quotes' % BASE_URL, json={
            'profile': profile_id,
            'sourceCurrency': currency,
            'sourceAmount': min(max_payout_amount, source_amount),
            'targetCurrency': 'CHF',
        }, headers=HEADERS)
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
        result = requests.post('%s/v1/transfers' % BASE_URL, json={
            'targetAccount': account_id,
            'quoteUuid': quote_id,
            'customerTransactionId': transactionId if transactionId else str(uuid.uuid4())
        }, headers=HEADERS)
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
            }, headers=HEADERS)
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

