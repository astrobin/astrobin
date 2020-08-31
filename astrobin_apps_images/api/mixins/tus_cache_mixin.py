from astrobin_apps_images.api import utils


class TusCacheMixin():
    def get_cached_property(self, property, object):
        return utils.get_cached_property(property, object)

    def set_cached_property(self, property, object, value):
        utils.set_cached_property(property, object, value)
