from __future__ import absolute_import

from hashlib import md5

from django.core.cache import cache

from celery import shared_task
from celery.utils.log import get_task_logger
from haystack.query import SearchQuerySet

from astrobin.models import Image


logger = get_task_logger(__name__)

LOCK_EXPIRE = 60 * 5 # Lock expires in 5 minutes

@shared_task()
def update_top100_ids():
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
