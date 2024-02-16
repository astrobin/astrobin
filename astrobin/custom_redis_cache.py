from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django_redis.cache import RedisCache
from redis.exceptions import TimeoutError

import logging

log = logging.getLogger(__name__)


class CustomRedisCache(RedisCache):
    def get(self, key, default=None, version=None, client=None):
        try:
            return super().get(key, default, version, client)
        except TimeoutError:
            log.debug(f"TimeoutError while getting key {key}")
            return None

    def set(self, key, value, timeout=DEFAULT_TIMEOUT, version=None, client=None):
        try:
            return super().set(key, value, timeout, version, client)
        except TimeoutError:
            log.debug(f"TimeoutError while setting key {key}")
            return False

    def delete(self, key, version=None, client=None):
        try:
            return super().delete(key, version, client)
        except TimeoutError:
            log.debug(f"TimeoutError while deleting key {key}")
            return False
