from django.db import models

class ImagesManager(models.Manager):
    def get_query_set(self):
        return super(ImagesManager, self).get_query_set()\
            .select_related(
                'user__userprofile',
            )\
            .prefetch_related(
                'image_of_the_day',
                'featured_gear',
                'revisions',
                'thumbnails',
            )


class PublicImagesManager(ImagesManager):
    def get_query_set(self):
        return super(PublicImagesManager, self).get_query_set()\
            .filter(is_wip = False)


class WipImagesManager(ImagesManager):
    def get_query_set(self):
        return super(WipImagesManager, self).get_query_set()\
            .filter(is_wip = True)

