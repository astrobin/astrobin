from django.db.models import Q

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

    def get_revisions(self, include_corrupted=False):
        revisions = ImageRevision.objects.filter(image=self.image)

        if not include_corrupted:
            revisions = revisions.filter(corrupted=False)

        return revisions

    def get_revisions_with_description(self, include_corrupted=False):
        return self.get_revisions(include_corrupted).exclude(Q(description=None) | Q(description=''))
