from safedelete.managers import SafeDeleteManager


class ImagesManager(SafeDeleteManager):
    def get_queryset(self):
        select_related = (
            'user',
            'user__userprofile',
            'iotd',
        )

        prefetch_related = (
            'pending_collaborators',
            'collaborators',
            'revisions',
            'thumbnails',
        )

        return super(ImagesManager, self) \
            .get_queryset() \
            .filter(uploader_in_progress__isnull=True) \
            .select_related(*select_related) \
            .prefetch_related(*prefetch_related)


# Use this manager when you don't want to do any prefetching.
class ImagesPlainManager(SafeDeleteManager):
    def get_queryset(self):
        return super(ImagesPlainManager, self).get_queryset().filter(
            uploader_in_progress__isnull=True
        )


class PublicImagesManager(ImagesManager):
    def get_queryset(self):
        return super(PublicImagesManager, self).get_queryset().filter(is_wip=False)


class PublicImagesPlainManager(SafeDeleteManager):
    def get_queryset(self):
        return super(PublicImagesPlainManager, self).get_queryset().filter(
            uploader_in_progress__isnull=True,
            is_wip=False
        )


class WipImagesManager(ImagesManager):
    def get_queryset(self):
        return super(WipImagesManager, self).get_queryset().filter(is_wip=True)


class UploadsInProgressImagesManager(ImagesManager):
    def get_queryset(self):
        from astrobin.models import Image
        return Image.all_objects.filter(deleted__isnull=True, uploader_in_progress=True)


class ImageRevisionsManager(SafeDeleteManager):
    def get_queryset(self):
        return super(ImageRevisionsManager, self).get_queryset().filter(uploader_in_progress__isnull=True)


class UploadsInProgressImageRevisionsManager(ImagesManager):
    def get_queryset(self):
        from astrobin.models import ImageRevision
        return ImageRevision.all_objects.filter(deleted__isnull=True, uploader_in_progress=True)

