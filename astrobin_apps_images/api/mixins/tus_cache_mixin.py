from django.core.cache import cache

from astrobin_apps_images.api import constants


class TusCacheMixin():
    def get_cached_property(self, property, image):
        return cache.get("tus-uploads/{}/{}".format(image.pk, property))

    def set_cached_property(self, property, image, value):
        cache.set("tus-uploads/{}/{}".format(image.pk, property), value, constants.TUS_CACHE_TIMEOUT)
