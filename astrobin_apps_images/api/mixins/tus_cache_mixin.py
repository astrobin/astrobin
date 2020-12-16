import logging

from astrobin_apps_images.api import utils

log = logging.getLogger('apps')


class TusCacheMixin():
    def get_cached_property(self, property, object):
        return utils.get_cached_property(property, object)

    def set_cached_property(self, property, object, value):
        log.debug("Chunked uploader (-) (%d): set in cache: %s = %s" % (object.pk, property, unicode(value)))
        utils.set_cached_property(property, object, value)
