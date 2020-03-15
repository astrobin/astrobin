from django.db.models import Q

from astrobin.models import Image, ImageRevision


class ImageService:
    image = None  # type: Image

    def __init__(self, image):
        # type: (Image) -> None
        self.image = image

    def get_revisions(self, include_corrupted=False):
        revisions = ImageRevision.objects.filter(image=self.image)

        if not include_corrupted:
            revisions = revisions.filter(corrupted=False)

        return revisions

    def get_revisions_with_description(self, include_corrupted=False):
        return self.get_revisions(include_corrupted).exclude(Q(description=None) | Q(description=''))
