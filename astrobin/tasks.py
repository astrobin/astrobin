from __future__ import absolute_import

# Python
from hashlib import md5

# Django
from django.core.cache import cache
from django.core.management import call_command

# Third party
from celery import shared_task
from celery.utils.log import get_task_logger
from haystack.query import SearchQuerySet

# AstroBin
from astrobin.models import Image


logger = get_task_logger(__name__)


@shared_task()
def test_task():
    logger.info('Test task')


@shared_task()
def update_top100_ids():
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
            cache.set('top100_ids', top100_ids, 60*60*24)
        finally:
            release_lock()
        return

    logger.debug(
        'Top100 ids task is already being run by another worker')


@shared_task()
def global_stats():
    sqs = SearchQuerySet()

    users = sqs.models(User).all().count()
    images = sqs.models(Image).all().count()

    integration = 0
    for i in sqs.models(Image).all():
        integration += i.integration
    integration = int(integration / 3600.0)

    gs = GlobalStat(
            users = users,
            images = images,
            integration = integration)
    gs.save()


@shared_task()
def sync_iotd_api():
    call_commang("image_of_the_day")


@shared_task()
def merge_gear():
    call_command("merge_gear")


@shared_task()
def hitcount_cleanup():
    call_command("hitcount_cleanup")


