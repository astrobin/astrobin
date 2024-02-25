import logging
import math
import mimetypes
import os
import re
import shutil
import subprocess
from collections import namedtuple
from datetime import timedelta
from functools import reduce
from typing import Optional, Union
from urllib.parse import urlencode

from actstream.models import Action
from annoying.functions import get_object_or_None
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.files import File
from django.core.files.images import get_image_dimensions
from django.core.files.temp import NamedTemporaryFile
from django.db.models import Q, QuerySet
from django.template.defaultfilters import floatformat
from django.utils.translation import ugettext as _

from django.urls import reverse
from hitcount.models import HitCount
from hitcount.views import HitCountMixin
from moviepy.editor import VideoFileClip
from numpy import average

from astrobin.enums import SolarSystemSubject, SubjectType
from astrobin.enums.display_image_download_menu import DownloadLimitation
from astrobin.enums.moderator_decision import ModeratorDecision
from astrobin.enums.mouse_hover_image import MouseHoverImage
from astrobin.models import (
    Collection, DeepSky_Acquisition, Image, ImageRevision, SOLAR_SYSTEM_SUBJECT_CHOICES,
    SolarSystem_Acquisition,
)
from astrobin.moon import MoonPhase
from astrobin.services.gear_service import GearService
from astrobin.services.utils_service import UtilsService
from astrobin.stories import ACTSTREAM_VERB_UPLOADED_IMAGE, add_story
from astrobin.utils import (
    base26_decode, base26_encode, decimal_to_degrees_minutes_seconds_string,
    decimal_to_hours_minutes_seconds_string,
)
from astrobin_apps_equipment.models import EquipmentBrandListing
from astrobin_apps_images.models import KeyValueTag, ThumbnailGroup
from astrobin_apps_notifications.tasks import push_notification_for_new_image
from astrobin_apps_notifications.utils import push_notification
from astrobin_apps_platesolving.models import Solution
from astrobin_apps_platesolving.solver import Solver
from astrobin_apps_premium.services.premium_service import PremiumService
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import is_free
from astrobin_apps_users.services import UserService
from common.services import AppRedirectionService, DateTimeService
from common.services.constellations_service import ConstellationException, ConstellationsService
from nested_comments.models import NestedComment
from toggleproperties.models import ToggleProperty

logger = logging.getLogger(__name__)


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

        return self.image.revisions.get(image=self.image, label=label)

    def get_final_revision_label(self):
        # type: () -> str
        # Avoid hitting the db by potentially exiting early
        if self.image.is_final:
            return '0'

        for r in self.image.revisions.all():
            if r.is_final:
                return r.label

        return '0'

    def get_final_revision(self) -> Union[Image, ImageRevision]:
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
        if not self.image.image_file:
            return None

        if revision_label is None or revision_label == '0':
            w, h = self.image.w, self.image.h

            if w == 0 or h == 0:
                try:
                    (w, h) = get_image_dimensions(self.image.image_file.file)
                except (ValueError, IOError) as e:
                    logger.warning(
                        "ImageService.get_default_cropping: unable to get image dimensions for %d: %s" % (
                            self.image.pk, str(e))
                    )
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
                            self.image.pk, str(e))
                    )
                    return '0,0,0,0'

        shorter_size = min(w, h)  # type: int
        x1 = int(w / 2.0 - shorter_size / 2.0)  # type: int
        x2 = int(w / 2.0 + shorter_size / 2.0)  # type: int
        y1 = int(h / 2.0 - shorter_size / 2.0)  # type: int
        y2 = int(h / 2.0 + shorter_size / 2.0)  # type: int

        return '%d,%d,%d,%d' % (x1, y1, x2, y2)

    def get_crop_box(self, alias, revision_label=None):
        if not self.image.image_file:
            return None

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
            revision_label
        )
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
                logger.warning(
                    "ImageService.get_crop_box: unable to get image dimensions for %d: %s" % (
                        target.pk, str(e))
                )
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
            uploaded__lt=DateTimeService.now() - timedelta(minutes=10)
        )

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

        thumbnails, created = ThumbnailGroup.objects.get_or_create(image=self.image, revision=revision_label)
        if getattr(thumbnails, alias) != url:
            setattr(thumbnails, alias, url)
            thumbnails.save()

            field = self.image.get_thumbnail_field(revision_label)
            cache_key = self.image.thumbnail_cache_key(field, alias, revision_label)
            cache.set(cache_key, url, 60 * 60 * 24)

    def delete_original(self):
        image: Image = self.image
        revisions: QuerySet = self.get_revisions()

        if image.solution:
            image.solution.delete()

        if not revisions.exists():
            image.delete()
            return

        new_original: ImageRevision = revisions.first()

        image.image_file = new_original.image_file
        image.video_file = new_original.video_file
        image.encoded_video_file = new_original.encoded_video_file
        image.encoding_error = new_original.encoding_error
        image.loop_video = new_original.loop_video
        image.square_cropping = new_original.square_cropping
        image.updated = new_original.uploaded
        image.w = new_original.w
        image.h = new_original.h
        image.is_final = image.is_final or new_original.is_final
        image.mouse_hover_image = new_original.mouse_hover_image \
            if new_original.mouse_hover_image != 'ORIGINAL' \
            else MouseHoverImage.SOLUTION

        if new_original.title:
            old_title = image.title
            appended_title = f' ({new_original.title})'
            ellipsis_ = '...'
            if len(old_title) > Image._meta.get_field('title').max_length - len(appended_title):
                old_title = old_title[:(Image._meta.get_field('title').max_length - len(appended_title)) - len(
                    ellipsis_
                )] + ellipsis_
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

        new_original.delete()
        image.thumbnails.filter(revision=new_original.label).delete()
        image.thumbnail_invalidate()

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
                        x.created_by.id if x.created_by else None,
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

    def remove_as_collaborator(self, user: User):
        self.image.collaborators.remove(user)

        thumb = self.image.thumbnail_raw('gallery', None, sync=True)

        push_notification(
            [self.image.user],
            user,
            'removed_self_as_collaborator',
            {
                'user': user,
                'image': self.image,
                'image_thumbnail': thumb.url if thumb else None,
            }
        )

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

    def promote_to_public_area(self, skip_notifications: bool, skip_activity_stream: bool):
        if self.image.is_wip:
            previously_published = self.image.published
            self.image.is_wip = False

            UserService(self.image.user).clear_gallery_image_list_cache()

            if not previously_published:
                if not skip_notifications:
                    push_notification_for_new_image.apply_async(args=(self.image.pk,), countdown=10)
                if not skip_activity_stream and self.image.moderator_decision == ModeratorDecision.APPROVED:
                    add_story(self.image.user, verb=ACTSTREAM_VERB_UPLOADED_IMAGE, action_object=self.image)

    def demote_to_staging_area(self):
        if not self.image.is_wip:
            self.image.is_wip = True

            UserService(self.image.user).clear_gallery_image_list_cache()

    def delete_stories(self):
        Action.objects.target(self.image).delete()
        Action.objects.action_object(self.image).delete()

    def generate_loading_placeholder(self, save=True):
        logger.debug('Generating loading placeholder for %s' % self.image)

        if self.image.w and self.image.h:
            w, h = self.image.w, self.image.h
        else:
            w, h = 1024, 1024

        placeholder_url = f'https://via.placeholder.com/{w}x{h}/222/333&text=PREVIEW NOT READY'
        response = UtilsService.http_with_retries(placeholder_url, stream=True)
        if response.status_code == 200:
            img_temp = NamedTemporaryFile()
            for block in response.iter_content(1024 * 8):
                if not block:
                    break
                img_temp.write(block)

            img_temp.flush()
            img_temp.seek(0)

            # Assuming `image` is the ImageField
            self.image.image_file.save("astrobin-video-placeholder.jpg", File(img_temp), save=False)

            if save:
                self.image.save(update_fields=['image_file'], keep_deleted=True)

    def get_local_video_file(self) -> File:
        chunk_size = 4096
        _, file_extension = os.path.splitext(self.image.uploader_name)

        filename = f'temp_video_file_{self.image.__class__.__name__}_{self.image.id}{file_extension}'
        temp_file_path = os.path.join('/astrobin-temporary-files/files', filename)

        if os.path.exists(temp_file_path):
            logger.debug(f'get_local_video_file: using existing temporary file {temp_file_path}')
            return File(open(temp_file_path, 'rb'))

        with self.image.video_file.open() as f:
            with open(temp_file_path, 'wb') as temp_file:
                while chunk := f.read(chunk_size):
                    temp_file.write(chunk)

        return File(open(temp_file_path, 'rb'))

    def get_deep_sky_acquisition_raw_data(self):
        deep_sky_acquisitions = DeepSky_Acquisition.objects.filter(image=self.image).order_by('date')

        data = {
            'dates': [],
            'frames': {},
            'integration': 0,
            'darks': [],
            'flats': [],
            'flat_darks': [],
            'bias': [],
            'bortle': [],
            'mean_sqm': [],
            'mean_fwhm': [],
            'temperature': [],
        }
        moon_age_list = []
        moon_illuminated_list = []

        for a in deep_sky_acquisitions.iterator():
            if a.date is not None and a.date not in data['dates']:
                data['dates'].append(a.date)
                m = MoonPhase(a.date)
                moon_age_list.append(m.age)
                moon_illuminated_list.append(m.illuminated * 100.0)

            if a.number and a.duration:
                key = ""
                if a.filter is not None or a.filter_2 is not None:
                    key = "filter(%s)" % (a.filter or a.filter_2)
                if a.iso is not None:
                    key += '-ISO(%d)' % a.iso
                if a.gain is not None:
                    key += '-gain(%.2f)' % a.gain
                if a.f_number is not None:
                    key += '-f_number(%.2f)' % a.f_number
                if a.sensor_cooling is not None:
                    key += '-temp(%d)' % a.sensor_cooling
                if a.binning is not None:
                    key += '-bin(%d)' % a.binning
                key += '-duration(%s)' % floatformat(a.duration, 4)

                try:
                    current_frames = data['frames'][key]['integration']
                except KeyError:
                    current_frames = '0x0"'

                integration_re = re.match(r'^(\d+)x(\d+)', current_frames)
                current_number = int(integration_re.group(1))

                data['frames'][key] = {}
                if a.filter_2:
                    data['frames'][key]['filter_url'] = f'/search/?{urlencode({"q": str(a.filter_2)})}'
                    data['frames'][key]['filter'] = str(a.filter_2)
                elif a.filter:
                    data['frames'][key]['filter_url'] = a.filter.get_absolute_url()
                    data['frames'][key]['filter'] = a.filter
                else:
                    data['frames'][key]['filter_url'] = '#'
                    data['frames'][key]['filter'] = ''
                data['frames'][key]['iso'] = 'ISO%d' % a.iso if a.iso is not None else ''
                data['frames'][key]['gain'] = '(gain: %.2f)' % a.gain if a.gain is not None else ''
                data['frames'][key]['f_number'] = f'f/{a.f_number}'.rstrip('0').rstrip('.') \
                    if a.f_number is not None else ''
                data['frames'][key]['sensor_cooling'] = '%d&deg;C' % a.sensor_cooling \
                    if a.sensor_cooling is not None else ''
                data['frames'][key]['binning'] = f'bin {a.binning}x{a.binning}' if a.binning else ''
                data['frames'][key]['integration'] = \
                    f'{current_number + a.number}x{floatformat(a.duration, 4).rstrip("0").rstrip(".")}'

                data['integration'] += a.duration * a.number

            for i in ['darks', 'flats', 'flat_darks', 'bias']:
                if a.filter and getattr(a, i):
                    data[i].append("%d" % getattr(a, i))
                elif getattr(a, i):
                    data[i].append(getattr(a, i))

            if a.bortle:
                data['bortle'].append(a.bortle)

            if a.mean_sqm:
                data['mean_sqm'].append(a.mean_sqm)

            if a.mean_fwhm:
                data['mean_fwhm'].append(a.mean_fwhm)

            if a.temperature:
                data['temperature'].append(a.temperature)

        return moon_age_list, moon_illuminated_list, data

    def get_deep_sky_acquisition_html(self):
        moon_age_list, moon_illuminated_list, data = self.get_deep_sky_acquisition_raw_data()

        def integration_html(integration):
            integration_re = re.match(r'^(\d+)x(\d+\.?\d*)', integration)
            number = int(integration_re.group(1))
            duration = float(integration_re.group(2))
            return f'<span class="number">{number}</span>' \
                   f'<span class="times-separator">&times;</span>' \
                   f'<span class="duration">{floatformat(duration, 4).rstrip("0").rstrip(".")}</span>' \
                   f'<span class="seconds-symbol">&Prime;</span> ' \
                   f'<span class="total-frame-integration">({DateTimeService.human_time_duration(number * duration)})</span>'

        def binning_html(binning):
            binning_re = re.match(r'^bin (\d)x(\d)', binning)

            if not binning_re:
                return binning

            x = int(binning_re.group(1))
            y = int(binning_re.group(2))
            return f'bin {x}<span class="times-separator">&times;</span>{y}'

        return [
            (
                _('Dates'),
                DateTimeService.format_date_ranges(data['dates'])
            ),
            (
                _('Frames'),
                '<div class="frames">' + '\n'.join(
                    "%s %s" % (
                        "<a href=\"%s\">%s</a>:" % (f[1]['filter_url'], f[1]['filter']) if f[1]['filter'] else '',
                        "%s %s %s %s %s %s" % (
                            integration_html(f[1]['integration']),
                            f[1]['iso'],
                            f[1]['gain'],
                            f[1]['f_number'],
                            f[1]['sensor_cooling'],
                            binning_html(f[1]['binning'])
                        ),
                    ) for f in sorted(data['frames'].items())
                ) +
                '</div>'
            ),
            (
                _('Integration'),
                DateTimeService.human_time_duration(data['integration'])
            ),
            (
                _('Darks'),
                '%d' % (int(reduce(lambda x, y: int(x) + int(y), data['darks'])) / len(data['darks']))
                if data['darks'] else 0
            ),
            (
                _('Flats'),
                '%d' % (int(reduce(lambda x, y: int(x) + int(y), data['flats'])) / len(data['flats']))
                if data['flats'] else 0
            ),
            (
                _('Flat darks'),
                '%d' % (int(reduce(lambda x, y: int(x) + int(y), data['flat_darks'])) / len(data['flat_darks']))
                if data['flat_darks'] else 0
            ),
            (
                _('Bias'),
                '%d' % (int(reduce(lambda x, y: int(x) + int(y), data['bias'])) / len(data['bias']))
                if data['bias'] else 0
            ),
            (
                _('Avg. Moon age'),
                "%.2f " % (average(moon_age_list),) + _("days") if moon_age_list else None
            ),
            (
                _('Avg. Moon phase'),
                "%.2f%%" % (average(moon_illuminated_list),) if moon_illuminated_list else None
            ),
            (
                _('Bortle Dark-Sky Scale'),
                "%.2f" % (average([float(x) for x in data['bortle']])) if data['bortle'] else None
            ),
            (
                _('Mean SQM'),
                "%.2f" % (average([float(x) for x in data['mean_sqm']])) if data['mean_sqm'] else None
            ),
            (
                _('Mean FWHM'),
                "%.2f" % (average([float(x) for x in data['mean_fwhm']])) if data['mean_fwhm'] else None
            ),
            (
                _('Temperature'),
                ("%.2f" % (average([float(x) for x in data['temperature']]))).rstrip('0').rstrip('.') + '&deg;C'
                if data['temperature'] else None
            ),
        ]

    def get_deep_sky_acquisition_text(self):
        moon_age_list, moon_illuminated_list, data = self.get_deep_sky_acquisition_raw_data()

        return (
            (
                _('Dates'),
                DateTimeService.format_date_ranges(data['dates'])
            ),
            (
                _('Frames'),
                '\n'.join(
                    "%s %s" % (
                        "%s:" % f[1]['filter'] if f[1]['filter'] else '',
                        "%s %s %s %s %s %s" % (
                            f[1]['integration'],
                            f[1]['iso'],
                            f[1]['gain'],
                            f[1]['f_number'],
                            f[1]['sensor_cooling'],
                            f[1]['binning']
                        ),
                    ) for f in sorted(data['frames'].items())
                )
            ),
            (
                _('Integration'),
                DateTimeService.human_time_duration(data['integration'], html=False)
            ),
            (
                _('Darks'),
                '%d' % (int(reduce(lambda x, y: int(x) + int(y), data['darks'])) / len(data['darks']))
                if data['darks'] else 0
            ),
            (
                _('Flats'),
                '%d' % (int(reduce(lambda x, y: int(x) + int(y), data['flats'])) / len(data['flats']))
                if data['flats'] else 0
            ),
            (
                _('Flat darks'),
                '%d' % (int(reduce(lambda x, y: int(x) + int(y), data['flat_darks'])) / len(data['flat_darks']))
                if data['flat_darks'] else 0
            ),
            (
                _('Bias'),
                '%d' % (int(reduce(lambda x, y: int(x) + int(y), data['bias'])) / len(data['bias']))
                if data['bias'] else 0
            ),
            (
                _('Avg. Moon age'),
                "%.2f " % (average(moon_age_list),) + _("days")) if moon_age_list else None,
            (
                _('Avg. Moon phase'),
                "%.2f%%" % (average(moon_illuminated_list),) if moon_illuminated_list else None
            ),
            (
                _('Bortle Dark-Sky Scale'),
                "%.2f" % (average([float(x) for x in data['bortle']])) if data['bortle'] else None
            ),
            (
                _('Mean SQM'),
                "%.2f" % (average([float(x) for x in data['mean_sqm']])) if data['mean_sqm'] else None
            ),
            (
                _('Mean FWHM'),
                "%.2f" % (average([float(x) for x in data['mean_fwhm']])) if data['mean_fwhm'] else None
            ),
            (
                _('Temperature'),
                ("%.2f" % (average([float(x) for x in data['temperature']]))).rstrip('0').rstrip('.') + 'C'
                if data['temperature'] else None
            )
        )

    def get_solar_system_acquisition_text(self):
        a = get_object_or_None(SolarSystem_Acquisition, image=self.image)

        if not a:
            return []

        results = []

        if a.date is not None:
            results.append((_('Date'), a.date.isoformat()))
        if a.time is not None:
            results.append((_('Time'), a.time))
        if a.frames is not None:
            results.append((_('Frames'), a.frames))
        if a.fps is not None:
            results.append((_('FPS'), floatformat(a.fps, 3).rstrip('0').rstrip('.')))
        if a.exposure_per_frame is not None:
            results.append((_('Exposure per frame'), floatformat(a.exposure_per_frame, 2).rstrip('0').rstrip('.')))
        if a.focal_length is not None:
            results.append((_('Focal length'), a.focal_length))
        if a.iso is not None:
            results.append(('ISO', a.iso))
        if a.gain is not None:
            results.append(('Gain', a.gain))
        if a.cmi is not None:
            results.append((_('CMI'), a.cmi))
        if a.cmii is not None:
            results.append((_('CMII'), a.cmii))
        if a.cmiii is not None:
            results.append((_('CMIII'), a.cmiii))
        if a.seeing is not None:
            results.append((_('Seeing'), a.seeing))
        if a.transparency is not None:
            results.append((_('Transparency'), a.transparency))

        return results

    def get_collection_tag_value(self, collection: Collection) -> Optional[str]:
        collection_tag_value = None

        if not collection or not collection.order_by_tag:
            return collection_tag_value

        collection_tag = KeyValueTag.objects.filter(
            key=collection.order_by_tag,
            image=self.image,
        ).first()
        if collection_tag:
            collection_tag_value = collection_tag.value

        return collection_tag_value

    def get_badges_cache(self, owner_or_superuser: bool, is_image_page: bool = False):
        from common.services.caching_service import CachingService, JSON_CACHE
        return CachingService.get(
            f'astrobin_image_badges__{self.image.pk}_{owner_or_superuser}_{is_image_page}',
            cache_name=JSON_CACHE
        )

    def set_badges_cache(self, badges, owner_or_superuser: bool, is_image_page: bool = False):
        from common.services.caching_service import CachingService, JSON_CACHE
        CachingService.set(
            f'astrobin_image_badges__{self.image.pk}_{owner_or_superuser}_{is_image_page}',
            badges, 60 * 60 * 24,
            cache_name=JSON_CACHE
        )

    def clear_badges_cache(self):
        from common.services.caching_service import CachingService, JSON_CACHE
        CachingService.delete(f'astrobin_image_badges__{self.image.pk}_True_True', cache_name=JSON_CACHE)
        CachingService.delete(f'astrobin_image_badges__{self.image.pk}_True_False', cache_name=JSON_CACHE)
        CachingService.delete(f'astrobin_image_badges__{self.image.pk}_False_True', cache_name=JSON_CACHE)
        CachingService.delete(f'astrobin_image_badges__{self.image.pk}_False_False', cache_name=JSON_CACHE)

    def update_toggleproperty_count(self, property_type):
        if hasattr(self.image, f'{property_type}_count'):
            Image.all_objects.filter(pk=self.image.pk).update(
                **{f'{property_type}_count': ToggleProperty.objects.filter(
                    content_type=ContentType.objects.get_for_model(self.image),
                    object_id=self.image.pk,
                    property_type=property_type
                ).count()}
            )

    def update_comment_count(self):
        Image.all_objects.filter(pk=self.image.pk).update(
            comment_count=NestedComment.objects.filter(
                content_type=ContentType.objects.get_for_model(self.image),
                object_id=self.image.pk,
            ).exclude(
                pending_moderation=True,
                deleted=True,
            ).count()
        )

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
        dec_dms = decimal_to_degrees_minutes_seconds_string(
            dec, degree_symbol='', minute_symbol='', second_symbol='',
            precision=0
        )

        try:
            return ConstellationsService.get_constellation('%s %s' % (ra_hms, dec_dms))
        except ConstellationException as e:
            logger.error('ConstellationException for solution %d: %s' % (solution.pk, str(e)))
            return None

    @staticmethod
    def is_image(path: str) -> bool:
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
    def is_video(path: str) -> bool:
        try:
            clip = VideoFileClip(path)
            clip.close()
            return True
        except OSError:
            return False

    @staticmethod
    def strip_video_metadata(path: str, mime_type: str) -> None:
        extension = mimetypes.guess_extension(mime_type)
        temp_path = f'{path}-stripped{extension}'

        cmd = [
            'ffmpeg',
            '-i', path,
            '-map_metadata', '-1',
            '-c:v', 'copy',
            '-c:a', 'copy',
            '-y',
            temp_path
        ]

        completed_process = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

        if completed_process.returncode != 0:
            logger.error(f"ffmpeg failed with error: {completed_process.stderr.decode('utf-8')}")
            return

        shutil.move(temp_path, path)

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

    @staticmethod
    def is_viewable_alias(alias: str) -> bool:
        # Small sizes are considered just thumbs, while regular and up are considered viewable.
        return alias in (
            'regular', 'regular_inverted', 'regular_sharpened',
            'regular_large', 'regular_large_inverted', 'regular_large_sharpened',
            'hd', 'hd_anonymized', 'hd_anonymized_crop', 'hd_inverted', 'hd_sharpened',
            'qhd', 'qhd_anonymized', 'qhd_inverted', 'qhd_sharpened',
            'real', 'real_inverted'
        )

    @staticmethod
    def is_badge_compatible_alias(alias: str) -> bool:
        return alias in (
            'thumb', 'gallery', 'gallery_inverted',
            'regular', 'regular_inverted', 'regular_sharpened',
            'regular_large', 'regular_large_inverted', 'regular_large_sharpened',
        )

    @staticmethod
    def is_tooltip_compatible_alias(alias: str) -> bool:
        return alias in (
            'gallery', 'gallery_inverted',
            'thumb',
        )

    @staticmethod
    def is_play_button_alias(alias: str) -> bool:
        return alias in (
            'iotd', 'iotd_mobile', 'iotd_candidate',
            'story', 'story_crop',
        )
