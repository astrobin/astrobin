from safedelete.managers import SafeDeleteManager


class ImagesManager(SafeDeleteManager):
    def get_queryset(self):
        return super(ImagesManager, self).get_queryset() \
            .select_related(
            'user__userprofile',
        ) \
            .prefetch_related(
            'image_of_the_day',
            'featured_gear',
            'revisions',
            'thumbnails',
        )


class PublicImagesManager(ImagesManager):
    def get_queryset(self):
        return super(PublicImagesManager, self).get_queryset() \
            .filter(is_wip=False)


class WipImagesManager(ImagesManager):
    def get_queryset(self):
        return super(WipImagesManager, self).get_queryset() \
            .filter(is_wip=True)
