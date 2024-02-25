import threading

from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django_redis.cache import RedisCache
from redis.exceptions import TimeoutError, ConnectionError

import logging

log = logging.getLogger(__name__)


class CustomRedisCache(RedisCache):
    def get_with_timeout(self, key, default=None, version=None, client=None):
        try:
            return super().get(key, default, version, client)
        except (TimeoutError, ConnectionError):
            log.debug(f"TimeoutError while getting key {key}")
            return None

    def get(self, key, default=None, version=None, client=None, operation_timeout=0.05):
        result = [default]
        thread = threading.Thread(
            target=lambda: result.insert(0, self.get_with_timeout(key, default, version, client))
        )

        thread.start()

        if operation_timeout in (0, None):
            thread.join()  # Wait indefinitely
        else:
            thread.join(operation_timeout)  # Wait for specified timeout
            if thread.is_alive():
                log.debug(f"Timeout while setting key {key}")
                return False

        return result[0]

    def set_with_timeout(self, key, value, timeout=DEFAULT_TIMEOUT, version=None, client=None):
        try:
            return super().set(key, value, timeout, version, client)
        except (TimeoutError, ConnectionError):
            log.debug(f"TimeoutError while setting key {key}")
            return False

    def set(self, key, value, timeout_val=DEFAULT_TIMEOUT, version=None, client=None, operation_timeout=0.05):
        result = [False]
        thread = threading.Thread(
            target=lambda: result.insert(0, self.set_with_timeout(key, value, timeout_val, version, client))
        )

        thread.start()

        if operation_timeout in (0, None):
            thread.join()
        else:
            thread.join(operation_timeout)
            if thread.is_alive():
                log.debug(f"Timeout while setting key {key}")
                return False

        return result[0]

