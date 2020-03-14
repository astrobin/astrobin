from astrobin.models import Image, ImageRevision


class ImageService:
    image = None  # type: Image

    def __init__(self, image):
        # type: (Image) -> None
        self.image = image

    def is_corrupted(self):
        # type: () -> bool
        if self.image.is_final and self.image.corrupted:
            return True

        try:
            final = self.image.revisions.get(label=self.image.get_final_revision_label())
            if final.corrupted:
                return True
        except ImageRevision.DoesNotExist:
            pass

        return False
