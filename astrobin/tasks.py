from __future__ import absolute_import

from django.core.cache import cache

from celery import shared_task
from haystack.query import SearchQuerySet

from astrobin.models import Image


@shared_task()
def update_top100_ids():
    sqs = SearchQuerySet().models(Image).order_by('-likes')
    top100_ids = [int(x.pk) for x in sqs][:100]
    cache.set('top100_ids', top100_ids, 60*60*24)
