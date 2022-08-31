import logging
import math
from collections import namedtuple
from datetime import timedelta

from annoying.functions import get_object_or_None
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.files.images import get_image_dimensions
from django.db.models import Q, QuerySet
from django.urls import reverse
from hitcount.models import HitCount
from hitcount.views import HitCountMixin

from astrobin.enums import SolarSystemSubject, SubjectType
from astrobin.enums.display_image_download_menu import DownloadLimitation
from astrobin.enums.moderator_decision import ModeratorDecision
from astrobin.models import Image, ImageRevision, SOLAR_SYSTEM_SUBJECT_CHOICES
from astrobin.services.gear_service import GearService
from astrobin.stories import add_story
from astrobin.utils import (
    base26_decode, base26_encode, decimal_to_degrees_minutes_seconds_string,
    decimal_to_hours_minutes_seconds_string,
)
from astrobin_apps_equipment.models import EquipmentBrandListing
from astrobin_apps_images.models import ThumbnailGroup
from astrobin_apps_notifications.tasks import push_notification_for_new_image
from astrobin_apps_platesolving.models import Solution
from astrobin_apps_platesolving.solver import Solver
from astrobin_apps_premium.services.premium_service import PremiumService
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import is_free
from common.services import AppRedirectionService, DateTimeService
from common.services.constellations_service import ConstellationException, ConstellationsService

logger = logging.getLogger("apps")


class ImageService:
    image = None  # type: Image

    def __init__(self, image=None):
        # type: (Image) -> None
        self.image = image

    def get_revision(self, label):
        # type: (str) -> ImageRevision
        if label is None or label == 0 or label == '0':
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

    def get_revisions(self, include_deleted=False) -> QuerySet:
        manager = ImageRevision.all_objects if include_deleted else ImageRevision.objects
        return manager.filter(image=self.image)

    def get_next_available_revision_label(self):
        # type: () -> str
        highest_label = 'A'
        for r in self.get_revisions(True):
            highest_label = r.label

        return base26_encode(base26_decode(highest_label) + 1)

    def get_revisions_with_title_or_description(self):
        # type: () -> QuerySet
        return self.get_revisions().exclude(
            Q(Q(title='') | Q(title__isnull=True)) &
            Q(Q(description='') | Q(description__isnull=True))
        )

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
        try:
            square_cropping_x0 = int(square_cropping.split(',')[0])
            square_cropping_y0 = int(square_cropping.split(',')[1])
            square_cropping_x1 = int(square_cropping.split(',')[2])
            square_cropping_y1 = int(square_cropping.split(',')[3])
        except (IndexError, ValueError) as e:
            return None

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
            moderator_decision=ModeratorDecision.UNDECIDED,
            uploaded__lt=DateTimeService.now() - timedelta(minutes=10))

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

    def set_thumb(self, alias: str, revision_label: str, url: str) -> None:
        if 'ERROR' in url:
            return

        field = self.image.get_thumbnail_field(revision_label)
        cache_key = self.image.thumbnail_cache_key(field, alias, revision_label)
        cache.set(cache_key, url, 60 * 60 * 24)

        thumbnails, created = ThumbnailGroup.objects.get_or_create(image=self.image, revision=revision_label)
        setattr(thumbnails, alias, url)
        thumbnails.save()

    def delete_original(self):
        image = self.image
        revisions = self.get_revisions()

        image.thumbnail_invalidate()

        if image.solution:
            image.solution.delete()

        if not revisions.exists():
            image.delete()
            return

        new_original = revisions.first()

        image.image_file = new_original.image_file
        image.updated = new_original.uploaded
        image.w = new_original.w
        image.h = new_original.h
        image.is_final = image.is_final or new_original.is_final

        if new_original.title:
            old_title = image.title
            appended_title = f' ({new_original.title})'
            ellipsis = '...'
            if len(old_title) > Image._meta.get_field('title').max_length - len(appended_title):
                old_title = old_title[:(Image._meta.get_field('title').max_length - len(appended_title)) - len(
                    ellipsis
                )] + ellipsis
            image.title = old_title + appended_title

        if image.description:
            image.description = f'{image.description}\n{new_original.description}' \
                if new_original.description \
                else new_original.description
        else:
            image.description = new_original.description

        image.save(keep_deleted=True)

        if new_original.solution:
            # Get the solution this way, I don't know why it wouldn't work otherwise
            content_type = ContentType.objects.get_for_model(ImageRevision)
            solution = Solution.objects.get(content_type=content_type, object_id=new_original.pk)
            solution.content_object = image
            solution.save()

        image.thumbnails.filter(revision=new_original.label).update(revision='0')
        new_original.delete()

    def get_enhanced_thumb_url(self, field, alias, revision_label, animated, secure, target_alias):
        get_enhanced_thumb_url = None
        enhanced_thumb_url = None

        if alias == 'regular' or alias == 'regular_sharpened':
            enhanced_alias = target_alias if alias == 'regular' else '%s_sharpened' % target_alias
            cache_key = self.image.thumbnail_cache_key(field, enhanced_alias, revision_label)
            if animated:
                cache_key += '_animated'
            enhanced_thumb_url = cache.get(cache_key)
            # Force HTTPS
            if enhanced_thumb_url and secure:
                enhanced_thumb_url = enhanced_thumb_url.replace('http://', 'https://', 1)

            # If we're testing, we want to bypass the placeholder thing and force-get
            # the enhanced thumb url.
            if enhanced_thumb_url is None and settings.TESTING:
                enhanced_thumb = self.image.thumbnail_raw(enhanced_alias, revision_label)
                if enhanced_thumb:
                    enhanced_thumb_url = enhanced_thumb.url

            if enhanced_thumb_url is None:
                get_enhanced_thumb_kwargs = {
                    'id': self.image.hash if self.image.hash else self.image.id,
                    'alias': enhanced_alias,
                }

                if revision_label is None or revision_label != 'final':
                    get_enhanced_thumb_kwargs['r'] = revision_label

                get_enhanced_thumb_url = reverse('image_thumb', kwargs=get_enhanced_thumb_kwargs)
                if animated:
                    get_enhanced_thumb_url += '?animated'

        return get_enhanced_thumb_url, enhanced_thumb_url

    def needs_premium_subscription_to_platesolve(self):
        valid_subscription = PremiumService(self.image.user).get_valid_usersubscription()
        return self.is_platesolvable() and \
               not self.is_platesolving_attempted() and \
               is_free(valid_subscription)

    def is_platesolvable(self):
        return \
            (self.image.subject_type == SubjectType.DEEP_SKY) or \
            (self.image.subject_type == SubjectType.WIDE_FIELD) or \
            (self.image.subject_type == SubjectType.SOLAR_SYSTEM and
             self.image.solar_system_main_subject == SolarSystemSubject.COMET)

    def is_platesolving_attempted(self):
        return self.image.solution and self.image.solution.status != Solver.MISSING

    def display_download_menu(self, user: User) -> bool:
        if self.image.download_limitation == DownloadLimitation.EVERYBODY:
            return True

        return user == self.image.user or user.is_superuser

    def record_hit(self, request):
        if request.user != self.image.user:
            UpdateHitCountResponse = namedtuple('UpdateHitCountResponse', 'hit_counted hit_message')
            hit_count: HitCount = HitCount.objects.get_for_object(self.image)
            hit_count_response: UpdateHitCountResponse = HitCountMixin.hit_count(request, hit_count)
            return hit_count_response

    def get_equipment_list(self, country=None):
        def item_data(item, version, explorer_url=None, unapproved=False, creator_id=None):
            data = {
                'id': str(item.id),
                'object': item,
                'type': item.__class__.__name__.lower(),
                'label': str(item) if version == 'NEW' else GearService(item).display_name(self.image.user),
                'version': version,
                'explorer_url': explorer_url,
                'unapproved': unapproved,
                'creator_id': creator_id
            }

            if version == 'LEGACY':
                # TODO: implement
                brand_listings = EquipmentBrandListing.objects.none()
            else:
                # TODO: implement
                brand_listings = EquipmentBrandListing.objects.none()

            data['brand_listings'] = brand_listings

            return data

        equipment_list = {
            'imaging_telescopes': [],
            'imaging_cameras': [],
            'mounts': [],
            'filters': [],
            'accessories': [],
            'software': [],
            'guiding_telescopes': [],
            'guiding_cameras': [],
        }

        for klass in equipment_list.keys():
            for x in getattr(self.image, f'{klass}_2').all():
                equipment_list[klass].append(
                    item_data(
                        x,
                        'NEW',
                        AppRedirectionService.redirect(f'/equipment/explorer/{x.klass.lower()}/{x.id}/{x.slug}'),
                        x.reviewer_decision is None,
                        x.created_by.id,
                    )
                )

            for x in getattr(self.image, klass).all():
                equipment_list[klass].append(item_data(x, 'LEGACY'))

        for x in getattr(self.image, 'focal_reducers').all():
            equipment_list['accessories'].append(item_data(x, 'LEGACY'))

        return equipment_list

    def invalidate_all_thumbnails(self):
        self.image.thumbnail_invalidate()

        revision: ImageRevision
        for revision in self.get_revisions().iterator():
            revision.thumbnail_invalidate()

    def get_error_thumbnail(self, revision_label, alias):
        w, h = self.image.w, self.image.h
        thumb_w, thumb_h = w, h
        if revision_label not in (0, '0'):
            try:
                revision = self.get_revision(revision_label)
                w, h = revision.w, revision.h
            except ImageRevision.DoesNotExist:
                pass

            thumb_w = min(settings.THUMBNAIL_ALIASES[''][alias]['size'][0], w)
            thumb_h = min(settings.THUMBNAIL_ALIASES[''][alias]['size'][0], h)

            if thumb_h == 0:
                thumb_h = math.floor(thumb_h * (w / float(thumb_w)))

        return f'https://via.placeholder.com/{thumb_w}x{thumb_h}/222/333&text=ERROR'

    def promote_to_public_area(self, skip_notifications):
        if self.image.is_wip:
            previously_published = self.image.published
            self.image.is_wip = False
            self.image.save(keep_deleted=True)

            if not previously_published:
                if not skip_notifications:
                    push_notification_for_new_image.apply_async(args=(self.image.pk,), countdown=10)
                add_story(self.image.user, verb='VERB_UPLOADED_IMAGE', action_object=self.image)

    @staticmethod
    def get_constellation(solution):
        if solution is None or solution.ra is None or solution.dec is None:
            return None

        ra = solution.advanced_ra if solution.advanced_ra else solution.ra
        ra_hms = decimal_to_hours_minutes_seconds_string(
            ra, hour_symbol='', minute_symbol='', second_symbol='',
            precision=0
        )

        dec = solution.advanced_dec if solution.advanced_dec else solution.dec
        dec_dms = decimal_to_degrees_minutes_seconds_string(dec, degree_symbol='', minute_symbol='', second_symbol='',
                                                            precision=0)

        try:
            return ConstellationsService.get_constellation('%s %s' % (ra_hms, dec_dms))
        except ConstellationException as e:
            logger.error('ConstellationException for solution %d: %s' % (solution.pk, str(e)))
            return None

    @staticmethod
    def verify_file(path):
        try:
            with open(path, 'rb') as f:
                from PIL import Image as PILImage
                trial_image = PILImage.open(f)
                trial_image.verify()
                f.seek(0)  # Because we opened it with PIL
        except Exception as e:
            logger.warning("Unable to read image file %s with PIL: %s" % (path, str(e)))
            return False

        return True

    @staticmethod
    def get_object(id, queryset):
        # hashes will always have at least a letter
        if id.isdigit():
            # old style numerical pk
            image = get_object_or_None(queryset, id=id)
            if image is not None:
                # if an image has a hash, we don't allow getting it by pk
                if image.hash is not None:
                    return None
                return image

        return get_object_or_None(queryset, hash=id)
