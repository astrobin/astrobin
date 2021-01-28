import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.core.files.images import get_image_dimensions
from django.db.models import Q

from astrobin.models import Image, ImageRevision, SOLAR_SYSTEM_SUBJECT_CHOICES
from astrobin.utils import base26_encode, base26_decode

logger = logging.getLogger("apps")

class ImageService:
    image = None  # type: Image

    def __init__(self, image=None):
        # type: (Image) -> None
        self.image = image

    def get_revision(self, label):
        # type: (str) -> ImageRevision
        if label is None or label is 0 or label is '0':
            raise ValueError("`label` must be a revision label (B or more)")

        if label == 'final':
            label = self.get_final_revision_label()

        return ImageRevision.objects.get(image=self.image, label=label)

    def get_final_revision_label(self):
        # type: () -> str
        # Avoid hitting the db by potentially exiting early
        if self.image.is_final:
            return '0'

        for r in self.image.revisions.all():
            if r.is_final:
                return r.label

        return '0'

    def get_final_revision(self):
        # type: () -> union[Image, ImageRevision]
        label = self.get_final_revision_label()

        if label == '0':
            return self.image

        return self.get_revision(label)

    def get_revisions(self, include_corrupted=False, include_deleted=False):
        # type: (bool, bool) -> QuerySet
        manager = ImageRevision.all_objects if include_deleted else ImageRevision.objects
        revisions = manager.filter(image=self.image)

        if not include_corrupted:
            revisions = revisions.filter(corrupted=False)

        return revisions

    def get_next_available_revision_label(self):
        # type: () -> str
        highest_label = 'A'
        for r in self.get_revisions(True, True):
            highest_label = r.label

        return base26_encode(base26_decode(highest_label) + 1)

    def get_revisions_with_description(self, include_corrupted=False):
        # type: (bool) -> QuerySet
        return self.get_revisions(include_corrupted).exclude(Q(description=None) | Q(description=''))

    def get_default_cropping(self, revision_label=None):
        if revision_label is None or revision_label == '0':
            w, h = self.image.w, self.image.h

            if w == 0 or h == 0:
                try:
                    (w, h) = get_image_dimensions(self.image.image_file.file)
                except (ValueError, IOError) as e:
                    logger.warning(
                        "ImageService.get_default_cropping: unable to get image dimensions for %d: %s" % (
                            self.image.pk, str(e)))
                    return '0,0,0,0'
        else:
            try:
                revision = self.get_revision(label=revision_label)
            except ImageRevision.DoesNotExist:
                return '0,0,0,0'

            w, h = revision.w, revision.h

            if w == 0 or h == 0:
                try:
                    (w, h) = get_image_dimensions(revision.image_file.file)
                except (ValueError, IOError) as e:
                    logger.warning(
                        "ImageService.get_default_cropping: unable to get image dimensions for %d: %s" % (
                            self.image.pk, str(e)))
                    return '0,0,0,0'

        shorter_size = min(w, h)  # type: int
        x1 = int(w / 2.0 - shorter_size / 2.0)  # type: int
        x2 = int(w / 2.0 + shorter_size / 2.0)  # type: int
        y1 = int(h / 2.0 - shorter_size / 2.0)  # type: int
        y2 = int(h / 2.0 + shorter_size / 2.0)  # type: int

        return '%d,%d,%d,%d' % (x1, y1, x2, y2)

    def get_crop_box(self, alias, revision_label=None):
        if revision_label in (None, '0', 0):
            target = self.image
        elif revision_label == 'final':
            target = self.get_final_revision()
        else:
            try:
                target = self.get_revision(label=revision_label)
            except ImageRevision.DoesNotExist:
                target = self.get_final_revision()

        square_cropping = target.square_cropping if target.square_cropping else self.get_default_cropping(
            revision_label)
        square_cropping_x0 = int(square_cropping.split(',')[0])
        square_cropping_y0 = int(square_cropping.split(',')[1])
        square_cropping_x1 = int(square_cropping.split(',')[2])
        square_cropping_y1 = int(square_cropping.split(',')[3])
        point_of_interest = {
            'x': int((square_cropping_x1 + square_cropping_x0) / 2),
            'y': int((square_cropping_y1 + square_cropping_y0) / 2),
        }

        w, h = target.w, target.h
        if w == 0 or h == 0:
            try:
                (w, h) = get_image_dimensions(target.image_file.file)
            except (ValueError, IOError, TypeError) as e:
                logger.warning("ImageService.get_crop_box: unable to get image dimensions for %d: %s" % (
                    target.pk, str(e)))
                return None

        crop_width = settings.THUMBNAIL_ALIASES[''][alias]['size'][0]
        crop_height = settings.THUMBNAIL_ALIASES[''][alias]['size'][1]

        if crop_width == 0 or crop_height == 0:
            return None

        crop_proportion = crop_width / float(crop_height)

        if crop_proportion == 1:
            return square_cropping
        else:
            if crop_width > crop_height:
                adjusted_crop_width = w
                adjusted_crop_height = int(w / crop_proportion)
            else:
                adjusted_crop_width = int(h / crop_proportion)
                adjusted_crop_height = h

        # Do x.
        remaining_width = w - adjusted_crop_width
        if remaining_width < 0:
            box_x0 = 0
            box_x1 = w
        else:
            box_x0_in_infinite_canvas = point_of_interest['x'] - (adjusted_crop_width / 2)
            box_x0 = max(0, min(box_x0_in_infinite_canvas, remaining_width))
            box_x1 = box_x0 + adjusted_crop_width

        # Do y.
        remaining_height = h - adjusted_crop_height
        if remaining_height < 0:
            box_y0 = 0
            box_y1 = h
        else:
            box_y0_in_infinite_canvas = point_of_interest['y'] - (adjusted_crop_height / 2)
            box_y0 = max(0, min(box_y0_in_infinite_canvas, remaining_height))
            box_y1 = box_y0 + adjusted_crop_height

        return '%d,%d,%d,%d' % (box_x0, box_y0, box_x1, box_y1)

    def get_subject_type_label(self):
        # type: () -> str
        for subject_type in Image.SUBJECT_TYPE_CHOICES:
            if self.image.subject_type == subject_type[0]:
                return subject_type[1]

    def get_solar_system_main_subject_label(self):
        # type: () -> str
        for solar_system_subject in SOLAR_SYSTEM_SUBJECT_CHOICES:
            if self.image.solar_system_main_subject == solar_system_subject[0]:
                return solar_system_subject[1]

    def get_images_pending_moderation(self):
        return Image.objects_including_wip.filter(
            moderator_decision=0,
            uploaded__lt = datetime.now() - timedelta(minutes=10))

    def get_hemisphere(self, revision_label=None):
        # type: (str) -> str

        target = None  # type: union[Image, ImageRevision]

        if revision_label is None or revision_label == '0':
            target = self.image
        else:
            try:
                target = self.get_revision(revision_label)
            except ImageRevision.DoesNotExist:
                return Image.HEMISPHERE_TYPE_UNKNOWN

        solution = target.solution  # type: Solution

        if solution is None or solution.dec is None:
            return Image.HEMISPHERE_TYPE_UNKNOWN

        return Image.HEMISPHERE_TYPE_NORTHERN if solution.dec >= 0 else Image.HEMISPHERE_TYPE_SOUTHERN

    @staticmethod
    def verify_file(path):
        try:
            with open(path) as f:
                from PIL import Image as PILImage
                trial_image = PILImage.open(f)
                trial_image.verify()
                f.seek(0)  # Because we opened it with PIL
        except Exception as e:
            return False

        return True
