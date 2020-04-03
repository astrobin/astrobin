from django.core.files.images import get_image_dimensions
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


    def get_default_cropping(self, revision_label = None):
        if revision_label is None or revision_label == '0':
            w, h = self.image.w, self.image.h

            if w == 0 or h == 0:
                (w, h) = get_image_dimensions(self.image.image_file.file)
        else:
            try:
                revision = self.image.revisions.get(label=revision_label)
            except ImageRevision.DoesNotExist:
                return '0,0,0,0'

            w, h = revision.w, revision.h

            if w == 0 or h == 0:
                (w, h) = get_image_dimensions(revision.image_file.file)

        shorter_size = min(w, h)  # type: int
        x1 = int(w / 2.0 - shorter_size / 2.0)  # type: int
        x2 = int(w / 2.0 + shorter_size / 2.0)  # type: int
        y1 = int(h / 2.0 - shorter_size / 2.0)  # type: int
        y2 = int(h / 2.0 + shorter_size / 2.0)  # type: int

        return '%d,%d,%d,%d' % (x1, y1, x2, y2)
