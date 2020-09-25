from safedelete.managers import SafeDeleteManager


class ImagesManager(SafeDeleteManager):
    def get_queryset(self):
        select_related = (
            'user',
            'user__userprofile',
            'iotd',
        )

        prefetch_related = (
            'revisions',
            'thumbnails',
            'solutions',
            'iotdvote_set',
        )

        return super(ImagesManager, self) \
            .get_queryset() \
            .select_related(*select_related) \
            .prefetch_related(*prefetch_related)


class PublicImagesManager(ImagesManager):
    def get_queryset(self):
        return super(PublicImagesManager, self).get_queryset() \
            .filter(is_wip=False)


class WipImagesManager(ImagesManager):
    def get_queryset(self):
        return super(WipImagesManager, self).get_queryset() \
            .filter(is_wip=True)
