from __future__ import absolute_import

import subprocess
from time import sleep

from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives
from django.core.management import call_command
from django_bouncy.models import Bounce
from haystack.query import SearchQuerySet

from astrobin.models import BroadcastEmail
from astrobin.utils import inactive_accounts
from astrobin_apps_images.models import ThumbnailGroup
from celery import shared_task

logger = get_task_logger(__name__)


@shared_task()
def test_task():
    logger.info('Test task begins')
    sleep(15)
    logger.info('Test task ends')


@shared_task(rate_limit="1/s", time_limit=5)
def update_top100_ids():
    from astrobin.models import Image

    LOCK_EXPIRE = 60 * 5 # Lock expires in 5 minutes
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
    subprocess.call(['scripts/contain_directory_size.sh', '/media/imagecache', '7'])


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

    if acquire_lock():
        try:
            image = Image.all_objects.get(pk=pk)
            thumb = image.thumbnail_raw(alias, options)

            if thumb:
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
