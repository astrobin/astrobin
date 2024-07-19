import hmac
import logging
import os
import random
import string
import unicodedata
import uuid
from typing import List, Optional
from urllib.parse import urlparse

import boto3
from django.apps import apps
from django.core.files.images import get_image_dimensions
from django.core.validators import MaxLengthValidator, MinLengthValidator, RegexValidator
from django.db.models import FileField
from django.urls import reverse
from easy_thumbnails.files import ThumbnailFile
from image_cropping import ImageRatioField

from astrobin.enums import SolarSystemSubject, SubjectType
from astrobin.enums.data_source import DataSource
from astrobin.enums.display_image_download_menu import DownloadLimitation
from astrobin.enums.full_size_display_limitation import FullSizeDisplayLimitation
from astrobin.enums.license import License
from astrobin.enums.moderator_decision import ModeratorDecision
from astrobin.enums.mouse_hover_image import MouseHoverImage
from astrobin.fields import CountryField, get_country_name
from astrobin.utils import generate_unique_hash
from astrobin_apps_equipment.models.equipment_brand_listing import EquipmentBrandListing
from astrobin_apps_equipment.models.equipment_item_listing import EquipmentItemListing
from astrobin_apps_notifications.services import NotificationsService
from astrobin_apps_users.services import UserService
from common.constants import GroupName
from common.services import DateTimeService
from common.upload_paths import (
    data_download_upload_path, image_upload_path, uncompressed_source_upload_path,
    video_upload_path,
)
from common.utils import get_sentinel_user
from common.validators import FileValidator

try:
    from hashlib import sha1
except ImportError:
    import sha
    sha1 = sha.sha

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.cache import cache, caches
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models
from django.db.models.signals import post_save
from django.template.defaultfilters import slugify
from django.utils import timezone
from django.utils.translation import pgettext, ugettext_lazy as _
from django.contrib.contenttypes.fields import GenericRelation, GenericForeignKey

from celery.result import AsyncResult
from model_utils.managers import InheritanceManager
from safedelete.models import SafeDeleteModel
from toggleproperties.models import ToggleProperty

from astrobin_apps_equipment.models import Telescope as TelescopeV2
from astrobin_apps_equipment.models import Camera as CameraV2
from astrobin_apps_equipment.models import Mount as MountV2
from astrobin_apps_equipment.models import Software as SoftwareV2
from astrobin_apps_equipment.models import Filter as FilterV2
from astrobin_apps_equipment.models import Accessory as AccessoryV2

from astrobin_apps_images.managers import (
    ImagesManager, ImagesPlainManager, PublicImagesManager, PublicImagesPlainManager, WipImagesManager,
    ImageRevisionsManager,
    UploadsInProgressImagesManager, UploadsInProgressImageRevisionsManager,
)
from astrobin_apps_notifications.utils import push_notification
from astrobin_apps_platesolving.models import Solution, PlateSolvingSettings, PlateSolvingAdvancedSettings
from nested_comments.models import NestedComment

log = logging.getLogger(__name__)


def image_hasher_function():
    model = apps.get_model('astrobin', 'Image')
    return generate_unique_hash(6, model.all_objects)


class HasSolutionMixin(object):
    @property
    def solution(self):
        # Try prefetch first
        if hasattr(self, '_prefetched_objects_cache') and 'solutions' in self._prefetched_objects_cache:
            return self._prefetched_objects_cache['solutions'][0] \
                if self._prefetched_objects_cache['solutions'] \
                else None

        # Then try request cache.
        from common.services.caching_service import CachingService

        cache_key = f'astrobin_solution_{self.__class__.__name__}_{self.pk}'
        solution = CachingService.get_from_request_cache(cache_key)
        if solution is not None or CachingService.is_in_request_cache(cache_key):
            return solution

        # Finally try the database
        solution = self.solutions.first()
        CachingService.set_in_request_cache(cache_key, solution)

        return solution


def image_hash() -> str:
    def generate_hash() -> str:
        return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(6))

    hash = generate_hash()
    while hash.isdigit() or Image.all_objects.filter(hash=hash).exists():
        hash = generate_hash()

    return hash


LICENSE_CHOICES = (
    (License.ALL_RIGHTS_RESERVED, _("None (All rights reserved)")),
    (License.ATTRIBUTION_NON_COMMERCIAL_SHARE_ALIKE, _("Attribution-NonCommercial-ShareAlike Creative Commons")),
    (License.ATTRIBUTION_NON_COMMERCIAL, _("Attribution-NonCommercial Creative Commons")),
    (License.ATTRIBUTION_NON_COMMERCIAL_NO_DERIVS, _("Attribution-NonCommercial-NoDerivs Creative Commons")),
    (License.ATTRIBUTION, _("Attribution Creative Commons")),
    (License.ATTRIBUTION_SHARE_ALIKE, _("Attribution-ShareAlike Creative Commons")),
    (License.ATTRIBUTION_NO_DERIVS, _("Attribution-NoDerivs Creative Commons")),
)

LANGUAGE_CHOICES = (
    ('en', _("English (US)")),
    ('en-GB', _("English (GB)")),
    ('it', _("Italian")),
    ('es', _("Spanish")),
    ('fr', _("French")),
    ('fi', _("Finnish")),
    ('de', _("German")),
    ('nl', _("Dutch")),
    ('tr', _("Turkish")),
    ('sq', _("Albanian")),
    ('pl', _("Polish")),
    ('pt', _("Portuguese")),
    ('el', _("Greek")),
    ('uk', _("Ukrainian")),
    ('ru', _("Russian")),
    ('ar', _("Arabic")),
    ('ja', _("Japanese")),
    ('zh-hans', _("Chinese (Simplified)")),
    ('hu', _("Hungarian")),
)

LANGUAGES = {
    'en': _("English (US)"),
    'en-GB': _("English (GB)"),
    'it': _("Italian"),
    'es': _("Spanish"),
    'fr': _("French"),
    'fi': _("Finnish"),
    'de': _("German"),
    'nl': _("Dutch"),
    'tr': _("Turkish"),
    'sq': _("Albanian"),
    'pl': _("Polish"),
    'pt': _("Portuguese"),
    'el': _("Greek"),
    'uk': _("Ukrainian"),
    'ru': _("Russian"),
    'ar': _("Arabic"),
    'ja': _("Japanese"),
    'zh-hans': _("Chinese (Simplified)"),
    'hu': _("Hungarian"),
}

SUBJECT_LABELS = {
    'PULSAR': _("Pulsars"),
    'GLOBUL': _("Globular clusters"),
    'OPENCL': _("Open clusters"),
    'NEBULA': _("Nebulae"),
    'PLNEBU': _("Planetary nebulae"),
    'GALAXY': _("Galaxies"),
}

SUBJECT_TYPES = {
    'Psr': 'PULSAR',
    'GlC': 'GLOBUL',
    'GCl': 'GLOBUL',
    'OpC': 'OPENCL',
    'HII': 'NEBULA',
    'RNe': 'NEBULA',
    'ISM': 'NEBULA',
    'sh ': 'NEBULA',
    'PN': 'PLNEBU',
    'LIN': 'GALAXY',
    'IG': 'GALAXY',
    'GiG': 'GALAXY',
    'Sy2': 'GALAXY',
    'G': 'GALAXY',
}

SOLAR_SYSTEM_SUBJECT_CHOICES = (
    (SolarSystemSubject.SUN, _("Sun")),
    (SolarSystemSubject.MOON, _("Earth's Moon")),
    (SolarSystemSubject.MERCURY, _("Mercury")),
    (SolarSystemSubject.VENUS, _("Venus")),
    (SolarSystemSubject.MARS, _("Mars")),
    (SolarSystemSubject.JUPITER, _("Jupiter")),
    (SolarSystemSubject.SATURN, _("Saturn")),
    (SolarSystemSubject.URANUS, _("Uranus")),
    (SolarSystemSubject.NEPTUNE, _("Neptune")),
    (SolarSystemSubject.MINOR_PLANET, _("Minor planet")),
    (SolarSystemSubject.COMET, _("Comet")),
    (SolarSystemSubject.OCCULTATION, _("Occultation")),
    (SolarSystemSubject.CONJUNCTION, _("Conjunction")),
    (SolarSystemSubject.PARTIAL_LUNAR_ECLIPSE, _("Partial lunar eclipse")),
    (SolarSystemSubject.TOTAL_LUNAR_ECLIPSE, _("Total lunar eclipse")),
    (SolarSystemSubject.PARTIAL_SOLAR_ECLIPSE, _("Partial solar eclipse")),
    (SolarSystemSubject.ANULAR_SOLAR_ECLIPSE, _("Anular solar eclipse")),
    (SolarSystemSubject.TOTAL_SOLAR_ECLIPSE, _("Total solar eclipse")),
    (SolarSystemSubject.METEOR_SHOWER, _("Meteor shower")),
    (SolarSystemSubject.OTHER, _("Other")),
)

WATERMARK_SIZE_CHOICES = (
    ('S', _("Small")),
    ('M', _("Medium")),
    ('L', _("Large")),
)

WATERMARK_POSITION_CHOICES = (
    (0, _("Center")),
    (1, _("Top left")),
    (2, _("Top center")),
    (3, _("Top right")),
    (4, _("Bottom left")),
    (5, _("Bottom center")),
    (6, _("Bottom right")),
)


class Gear(models.Model):
    created = models.DateTimeField(
        auto_now_add=True,
        editable=False,
    )

    make = models.CharField(
        verbose_name=_("Make"),
        help_text=_("The make, brand, producer or developer of this product."),
        max_length=128,
        null=True,
        blank=True,
    )

    name = models.CharField(
        verbose_name=_("Name"),
        help_text=_(
            "Just the name of this product, without any properties or personal customizations. Try to use the international name, in English language, if applicable. This name is shared among all users on AstroBin."),
        max_length=128,
        null=False,
        blank=False,
    )

    master = models.ForeignKey('self', null=True, editable=False, on_delete=models.SET_NULL)

    updated = models.DateTimeField(
        editable=False,
        auto_now=True,
        null=True,
        blank=True,
    )

    equipment_brand_listings = models.ManyToManyField(
        EquipmentBrandListing,
        related_name='gear_items',
        editable=False,
    )

    equipment_item_listings = models.ManyToManyField(
        EquipmentItemListing,
        related_name='gear_items',
        editable=False,
    )

    migration_flag_moderator_lock = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='migrated_gear_item_locks',
    )

    migration_flag_moderator_lock_timestamp = models.DateTimeField(
        null=True,
        blank=True,
    )

    def __str__(self):
        make = self.get_make()
        name = self.get_name()

        if make and make.lower() in name.lower():
            return name
        if not make or make == '':
            return name
        return "%s %s" % (make, name)

    def attributes(self):
        return []

    def get_absolute_url(self):
        return '/search/?q=%s' % str(self)

    def slug(self):
        return slugify("%s %s" % (self.get_make(), self.get_name()))

    def get_make(self):
        if self.make:
            return self.make
        return ''

    def get_name(self):
        return self.name

    class Meta:
        app_label = 'astrobin'
        ordering = ('-updated',)


class GearUserInfo(models.Model):
    gear = models.ForeignKey(
        Gear,
        editable=False,
        on_delete=models.CASCADE
    )

    user = models.ForeignKey(
        User,
        editable=False,
        on_delete=models.CASCADE
    )

    alias = models.CharField(
        verbose_name=_("Alias"),
        help_text=_("A descriptive name, alias or nickname for your own copy of this product."),
        max_length=128,
        null=True,
        blank=True,
    )

    comment = models.TextField(
        verbose_name=_("Comment"),
        help_text=_("Information, description or comment about your own copy of this product."),
        null=True,
        blank=True,
    )

    modded = models.NullBooleanField(
        verbose_name=_("Modded"),
        help_text=_("Has this object been modified for astrophotography? (especially applicable to cameras)"),
        null=True,
        blank=True,
    )

    def __str__(self):
        name: str

        if self.alias:
            name = f'{self.alias} ({str(self.gear)})'
        else:
            name = str(self.gear)

        if self.modded:
            name = f'{name} ({pgettext("Pertaining to cameras, e.g. a modified Canon", "modified")})'

        return name

    class Meta:
        app_label = 'astrobin'
        unique_together = ('gear', 'user')


class GearMigrationStrategy(models.Model):
    gear = models.ForeignKey(
        Gear,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name='migration_strategies',
    )

    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='gear_migration_strategies',
    )

    migration_flag = models.CharField(
        max_length=16,
        null=False,
        blank=False,
        choices=(
            ('WRONG_TYPE', 'This item is the wrong type'),
            ('MULTIPLE_ITEMS', 'This item collates multiple objects'),
            ('NOT_ENOUGH_INFO', 'This item does not have enough information to decide on a migration strategy'),
            ('MIGRATE', 'This item is ready for migration')
        ),
    )

    migration_flag_timestamp = models.DateTimeField(
        null=True,
        blank=True,
    )

    migration_content_type = models.ForeignKey(
        ContentType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    migration_object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    migration_content_object = GenericForeignKey(
        'migration_content_type',
        'migration_object_id',
    )

    migration_flag_moderator = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='migrated_gear_items',
    )

    migration_flag_reviewer_lock = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_for_migration_gear_item_locks',
    )

    migration_flag_reviewer_lock_timestamp = models.DateTimeField(
        null=True,
        blank=True,
    )

    migration_flag_reviewer = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_for_migration_gear_items',
    )

    migration_flag_reviewer_decision = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        choices=[
            ("APPROVED", "Approved"),
        ],
    )

    applied = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        app_label = 'astrobin'
        unique_together = (
            'gear',
            'user',
        )
        ordering=('-pk',)


class GearRenameProposal(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )

    gear = models.ForeignKey(
        Gear,
        on_delete=models.CASCADE,
    )

    created = models.DateTimeField(
        auto_now_add=True,
        editable=False,
    )

    old_make = models.CharField(
        max_length=128,
        null=True,
        blank=True,
    )

    old_name = models.CharField(
        max_length=128,
        null=False,
        blank=False,
    )

    new_make = models.CharField(
        max_length=128,
        null=False,
        blank=False,
    )

    new_name = models.CharField(
        max_length=128,
        null=False,
        blank=False,
    )

    status = models.CharField(
        max_length=13,
        null=False,
        blank=False,
        default='PENDING',
        choices=(
            ('PENDING', _('Pending')),
            ('APPROVED', _('Approved')),
            ('AUTO_APPROVED', _('Automatically approved')),
            ('REJECTED', _('Rejected')),
        )
    )

    reject_reason = models.TextField(
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True
        unique_together = ['user', 'gear']


class CameraRenameProposal(GearRenameProposal):
    type = models.CharField(
        max_length=128,
        null=True,
        blank=True,
    )

    modified = models.BooleanField(
        default=False,
    )

    cooled = models.BooleanField(
        default=False,
    )

    sensor_make = models.CharField(
        max_length=128,
        null=True,
        blank=True,
    )

    sensor_name = models.CharField(
        max_length=128,
        null=True,
        blank=True,
    )


class GearRenameRecord(models.Model):
    gear = models.ForeignKey(
        Gear,
        editable=False,
        on_delete=models.CASCADE,
        unique=True,
    )

    created = models.DateTimeField(
        auto_now_add=True,
        editable=False,
    )

    old_make = models.CharField(
        max_length=128,
        null=True,
        blank=True,
    )

    old_name = models.CharField(
        max_length=128,
        null=False,
        blank=False,
    )

    new_make = models.CharField(
        max_length=128,
        null=False,
        blank=False,
    )

    new_name = models.CharField(
        max_length=128,
        null=False,
        blank=False,
    )


class Telescope(Gear):
    TELESCOPE_TYPES = (
        ("REFR ACHRO", _("Refractor: achromatic")),
        ("REFR SEMI-APO", _("Refractor: semi-apochromatic")),
        ("REFR APO", _("Refractor: apochromatic")),
        ("REFR NON-ACHRO GALILEAN", _("Refractor: non-achromatic Galilean")),
        ("REFR NON-ACHRO KEPLERIAN", _("Refractor: non-achromatic Keplerian")),
        ("REFR SUPERACHRO", _("Refractor: superachromat")),

        ("REFL DALL-KIRKHAM", _("Reflector: Dall-Kirkham")),
        ("REFL NASMYTH", _("Reflector: Nasmyth")),
        ("REFL RITCHEY CHRETIEN", _("Reflector: Ritchey Chretien")),
        ("REFL GREGORIAN", _("Reflector: Gregorian")),
        ("REFL HERSCHELLIAN", _("Reflector: Herschellian")),
        ("REFL NEWTONIAN", _("Reflector: Newtonian")),

        ("CATA ARGUNOV-CASSEGRAIN", _("Catadioptric: Argunov-Cassegrain")),
        ("CATA KLEVTSOV-CASSEGRAIN", _("Catadioptric: Klevtsov-Cassegrain")),
        ("CATA LURIE-HOUGHTON", _("Catadioptric: Lurie-Houghton")),
        ("CATA MAKSUTOV", _("Catadioptric: Maksutov")),
        ("CATA MAKSUTOV-CASSEGRAIN", _("Catadioptric: Maksutov-Cassegrain")),
        ("CATA MAKSUTOV-NEWTONIAN", _("Catadioptric: Maksutov-Newtonian")),
        ("CATA MOD DALL-KIRKHAM", _("Catadioptric: modified Dall-Kirkham")),
        ("CATA SCHMIDT CAMERA", _("Catadioptric: Schmidt camera")),
        ("CATA SCHMIDT-CASSEGRAIN", _("Catadioptric: Schmidt-Cassegrain")),
        ("CATA ACF SCHMIDT-CASSEGRAIN", _("Catadioptric: ACF Schmidt-Cassegrain")),
        ("CATA ROWE-ACKERMANN SCHMIDT", _("Catadioptric: Rowe-Atkinson Schmidt astrograph")),
        ("CAMERA LENS", _("Camera lens")),
        ("BINOCULARS", _("Binoculars")),
    )

    aperture = models.DecimalField(
        verbose_name=_("Aperture"),
        help_text=_("(in mm)"),
        null=True,
        blank=True,
        max_digits=8,
        decimal_places=2,
    )

    focal_length = models.DecimalField(
        verbose_name=_("Focal length"),
        help_text=_("(in mm)"),
        null=True,
        blank=True,
        max_digits=8,
        decimal_places=2,
    )

    type = models.CharField(
        verbose_name=_("Type"),
        null=True,
        blank=True,
        max_length=64,
        choices=TELESCOPE_TYPES,
    )

    def attributes(self):
        return super(Telescope, self).attributes() + \
               [('aperture', _("mm")), ('focal_length', _("mm"))]

    def type_label(self):
        if self.type is not None:
            for i in self.TELESCOPE_TYPES:
                if self.type == i[0]:
                    return i[1]

        return _("Unknown")

    class Meta:
        app_label = 'astrobin'


class Mount(Gear):
    max_payload = models.DecimalField(
        verbose_name=_("Max. payload"),
        help_text=_("(in kg)"),
        null=True,
        blank=True,
        max_digits=6,
        decimal_places=2,
    )

    pe = models.DecimalField(
        verbose_name=_("Periodic error"),
        help_text=_("(peak to peak, in arcseconds)"),
        null=True,
        blank=True,
        max_digits=6,
        decimal_places=2,
    )

    def attributes(self):
        return super(Mount, self).attributes() + \
               [('max_payload', _("kg")), ('pe', "\"")]

    class Meta:
        app_label = 'astrobin'


class Camera(Gear):
    CAMERA_TYPES = (
        ("CCD", _("CCD")),
        ("DSLR", _("DSLR")),
        ("GUIDER/PLANETARY", _("Guider/Planetary")),
        ("FILM", _("Film")),
        ("COMPACT", _("Compact")),
        ("VIDEO", _("Video camera")),
    )

    pixel_size = models.DecimalField(
        verbose_name=_("Pixel size"),
        help_text=_("(in &mu;m)"),
        null=True,
        blank=True,
        max_digits=6,
        decimal_places=2,
    )

    sensor_width = models.DecimalField(
        verbose_name=_("Sensor width"),
        help_text=_("(in mm)"),
        null=True,
        blank=True,
        max_digits=6,
        decimal_places=2,
    )

    sensor_height = models.DecimalField(
        verbose_name=_("Sensor height"),
        help_text=_("(in mm)"),
        null=True,
        blank=True,
        max_digits=6,
        decimal_places=2,
    )

    type = models.CharField(
        verbose_name=_("Type"),
        null=True,
        blank=True,
        max_length=64,
        choices=CAMERA_TYPES,
    )

    def attributes(self):
        return super(Camera, self).attributes() + \
               [('sensor_width', _("mm")), ('sensor_height', _("mm")), ('pixel_size', _("&mu;m"))]

    def type_label(self):
        if self.type is not None:
            for i in self.CAMERA_TYPES:
                if self.type == i[0]:
                    return i[1]

        return _("Unknown")

    class Meta:
        app_label = 'astrobin'


class FocalReducer(Gear):
    class Meta:
        app_label = 'astrobin'


class Software(Gear):
    SOFTWARE_TYPES = (
        ("OPEN_SOURCE_OR_FREEWARE", _("Open source or freeware")),
        ("PAID", _("Paid")),
    )

    type = models.CharField(
        verbose_name=_("Type"),
        null=True,
        blank=True,
        max_length=64,
        choices=SOFTWARE_TYPES,
    )

    class Meta:
        app_label = 'astrobin'


class Filter(Gear):
    FILTER_TYPES = (
        ("CLEAR_OR_COLOR", _("Clear or color")),

        ("BROAD HA", _("Broadband: H-Alpha")),
        ("BROAD HB", _("Broadband: H-Beta")),
        ("BROAD SII", _("Broadband: S-II")),
        ("BROAD OIII", _("Broadband: O-III")),
        ("BROAD NII", _("Broadband: N-II")),

        ("NARROW HA", _("Narrowband: H-Alpha")),
        ("NARROW HB", _("Narrowband: H-Beta")),
        ("NARROW SII", _("Narrowband: S-II")),
        ("NARROW OIII", _("Narrowband: O-III")),
        ("NARROW NII", _("Narrowband: N-II")),

        ("LP", _("Light pollution suppression")),
        ("PLANETARY", _("Planetary")),
        ("UHC", _("UHC: Ultra High Contrast")),

        ("OTHER", _("Other")),
    )

    type = models.CharField(
        verbose_name=_("Type"),
        null=True,
        blank=True,
        max_length=64,
        choices=FILTER_TYPES,
    )

    bandwidth = models.DecimalField(
        verbose_name=_("Bandwidth"),
        help_text=_("(in nm)"),
        null=True,
        blank=True,
        max_digits=6,
        decimal_places=2,
    )

    def attributes(self):
        return super(Filter, self).attributes() + \
               [('bandwidth', _("nm"))]

    class Meta:
        app_label = 'astrobin'


class Accessory(Gear):
    pass

    class Meta:
        app_label = 'astrobin'


def build_catalog_and_name(obj, name):
    split = name.split(' ')
    if len(split) > 1:
        cat = split[0]
        del (split[0])
        name = ' '.join(split)

        setattr(obj, 'catalog', cat)
    setattr(obj, 'name', name)


# TODO: unify Image and ImageRevision
# TODO: remember that thumbnails must return 'final' version
# TODO: notifications for gear and subjects after upload
# TODO: this makes animated gifs static :-(
class Image(HasSolutionMixin, SafeDeleteModel):
    BINNING_CHOICES = (
        (1, '1x1'),
        (2, '2x2'),
        (3, '3x3'),
        (4, '4x4'),
    )

    ACQUISITION_TYPES = (
        'REGULAR',
        'EAA',
        'LUCKY',
        'DRAWING',
        'OTHER',
    )

    ACQUISITION_TYPE_CHOICES = (
        ('REGULAR', _("Regular (e.g. medium/long exposure with a CCD or DSLR)")),
        ('EAA', _("Electronically-Assisted Astronomy (EAA, e.g. based on a live video feed)")),
        ('LUCKY', _("Lucky imaging")),
        ('DRAWING', _("Drawing/Sketch")),
        ('OTHER', _("Other/Unknown")),
    )

    SUBJECT_TYPE_CHOICES = (
        (None, "---------"),
        (SubjectType.DEEP_SKY, _("Deep sky object or field")),
        (SubjectType.SOLAR_SYSTEM, _("Solar system body or event")),
        (SubjectType.WIDE_FIELD, _("Extremely wide field")),
        (SubjectType.STAR_TRAILS, _("Star trails")),
        (SubjectType.NORTHERN_LIGHTS, _("Northern lights")),
        (SubjectType.NOCTILUCENT_CLOUDS, _("Noctilucent clouds")),
        (SubjectType.LANDSCAPE, _("Landscape")),
        (SubjectType.ARTIFICIAL_SATELLITE, _("Artificial satellite")),
        (SubjectType.GEAR, _("Gear")),
        (SubjectType.OTHER, _("Other")),
    )

    DATA_SOURCE_TYPES = (
        DataSource.BACKYARD,
        DataSource.TRAVELLER,
        DataSource.OWN_REMOTE,
        DataSource.AMATEUR_HOSTING,
        DataSource.PUBLIC_AMATEUR_DATA,
        DataSource.PRO_DATA,
        DataSource.MIX,
        DataSource.OTHER,
        DataSource.UNKNOWN,
    )

    DATA_SOURCE_CHOICES = (
        (None, "---------"),
        (_("Self acquired"), (
            (DataSource.BACKYARD, _("Backyard")),
            (DataSource.TRAVELLER, _("Traveller")),
            (DataSource.OWN_REMOTE, _("Own remote observatory")),
        )),
        (_("Downloaded"), (
            (DataSource.AMATEUR_HOSTING, _("Amateur hosting facility")),
            (DataSource.PUBLIC_AMATEUR_DATA, _("Public amateur data")),
            (DataSource.PRO_DATA, _("Professional, scientific grade data")),
        )),
        (_("Other"), (
            (DataSource.MIX, _("Mix of multiple sources")),
            (DataSource.OTHER, _("None of the above")),
            (DataSource.UNKNOWN, _("Unknown")),
        )),
    )

    REMOTE_OBSERVATORY_CHOICES = (
        (None, "---------"),
        ("OWN", _("Non-commercial independent facility")),
        (None, "---------"),
        ("ALNI", "Alnitak Remote Observatories"),
        ("AC", "AstroCamp"),
        ("AHK", "Astro Hostel Krasnodar"),
        ("ACRES", "Astronomy Acres"),
        ("AOWA", "Astro Observatories Western Australia"),
        ("ATLA", "Atlaskies Observatory"),
        ("CS", "ChileScope"),
        ("DMA", "Dark Matters Astrophotography"),
        ("DSNM", "Dark Sky New Mexico"),
        ("DSP", "Dark Sky Portal"),
        ("DSV", "Deepsky Villa"),
        ("DSC", "DeepSkyChile"),
        ("DSPR", "Deep Space Products Remote"),
        ("DSW", "DeepSkyWest"),
        ("eEyE", "e-EyE Extremadura"),
        ("EITS", "Eye In The Sky"),
        ("GFA", "Goldfield Astronomical Observatory"),
        ("GMO", "Grand Mesa Observatory"),
        ("HAKOS", "Hakos Astro Farm"),
        ("HAWK", "HAWK Observatory"),
        ("HCRO", "Howling Coyote Remote Observatories (HCRO)"),
        ("HMO", "Heaven's Mirror Observatory"),
        ("IC", "IC Astronomy Observatories"),
        ("ITU", "Image The Universe"),
        ("INS", "Insight Observatory"),
        ("ITELESCO", "iTelescope"),
        ("LGO", "Lijiang Gemini Observatory"),
        ("MARIO", "Marathon Remote Imaging Observatory (MaRIO)"),
        ("NMS", "New Mexico Skies"),
        ("OES", "Observatorio El Sauce"),
        ("PSA", "PixelSkies"),
        ("REM", "RemoteSkies.net"),
        ("REMSG", "Remote Skygems"),
        ("RLD", "Riverland Dingo Observatory"),
        ("ROBO", "RoboScopes"),
        ("ROCKCHUCK", "Rockchuck Summit Observatory"),
        ("SS", "Sahara Sky"),
        ("SPVO", "San Pedro Valley Observatory"),
        ("SRO", "Sierra Remote Observatories"),
        ("SRO2", "Sky Ranch Observatory"),
        ("SPOO", "SkyPi Remote Observatory"),
        ("SLO", "Slooh"),
        ("SPI", "Spica"),
        ("SSLLC", "Stellar Skies LLC"),
        ("SKIESAWAY", "SkiesAway Remote Observatories"),
        ("STARFRONT", "Starfront Observatories"),
        ("TAIYUGE", "TaiYuge Observatory"),
        ("TELI", "Telescope Live"),
        ("TREV", "Trevinca Skies"),
        ("UDRO", "Utah Desert Remote Observatories"),
        ("WTO", "West Texas Observatory (WTO)"),
        ("YINHE", "YinHe Observatory"),
        ("YUNLING", "Yunling Observatory"),

        ("OTHER", _("None of the above"))
    )

    MOUSE_HOVER_CHOICES = [
        (MouseHoverImage.NOTHING, _("Nothing")),
        (MouseHoverImage.SOLUTION, _("Plate-solution annotations (if available)")),
        (MouseHoverImage.INVERTED, _("Inverted monochrome")),
    ]

    FULL_SIZE_DISPLAY_LIMITATION_CHOICES = [
        (FullSizeDisplayLimitation.EVERYBODY, _('Everybody')),
        (FullSizeDisplayLimitation.PAYING_MEMBERS_ONLY, _('Paying members only')),
        (FullSizeDisplayLimitation.MEMBERS_ONLY, _('Members only')),
        (FullSizeDisplayLimitation.ME_ONLY, _('Me only')),
        (FullSizeDisplayLimitation.NOBODY, _('Nobody')),
    ]

    DOWNLOAD_LIMITATION_CHOICES = [
        (DownloadLimitation.EVERYBODY, _('Everybody')),
        (DownloadLimitation.ME_ONLY, _('Me only')),
    ]

    GEAR_CLASS_LOOKUP = {
        'imaging_telescopes': Telescope,
        'guiding_telescopes': Telescope,
        'mounts': Mount,
        'imaging_cameras': Camera,
        'guiding_cameras': Camera,
        'focal_reducers': FocalReducer,
        'software': Software,
        'filters': Filter,
        'accessories': Accessory,
    }

    HEMISPHERE_TYPE_UNKNOWN = 'HEMISPHERE_TYPE_UNKNOWN'
    HEMISPHERE_TYPE_NORTHERN = 'HEMISPHERE_TYPE_NORTHERN'
    HEMISPHERE_TYPE_SOUTHERN = 'HEMISPHERE_TYPE_SOUTHERN'

    solutions = GenericRelation(Solution)

    corrupted = models.BooleanField(
        default=False
    )

    recovered = models.DateTimeField(
        null=True,
        blank=True
    )

    recovery_ignored = models.DateTimeField(
        null=True,
        blank=True
    )

    hash = models.CharField(
        max_length=6,
        default=image_hasher_function,
        null=True,
        unique=True
    )

    uploader_in_progress = models.NullBooleanField(
        default=None,
        editable=False
    )

    uploader_name = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        editable=False,
    )

    uploader_upload_length = models.PositiveIntegerField(
        null=True,
        blank=True,
        editable=False,
    )

    uploader_offset = models.PositiveIntegerField(
        null=True,
        blank=True,
        editable=False,
    )

    uploader_expires = models.DateTimeField(
        null=True,
        blank=True,
        editable=False,
    )

    uploader_metadata = models.TextField(
        null=True,
        blank=True,
        editable=False,
    )

    uploader_temporary_file_path = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        editable=False,
    )

    title = models.CharField(
        max_length=128,
        verbose_name=_("Title"),
    )

    acquisition_type = models.CharField(
        verbose_name=_("Acquisition type"),
        choices=ACQUISITION_TYPE_CHOICES,
        max_length=32,
        null=False,
        default='REGULAR'
    )

    subject_type = models.CharField(
        verbose_name=_("Subject type"),
        choices=SUBJECT_TYPE_CHOICES,
        max_length=18,
        null=False,
    )

    data_source = models.CharField(
        verbose_name=_("Data source"),
        help_text=_("Where does the data for this image come from?"),
        max_length=32,
        choices=DATA_SOURCE_CHOICES,
        null=False,
        blank=False,
    )

    remote_source = models.CharField(
        verbose_name=_("Remote data source"),
        help_text=_("Which remote hosting facility did you use to acquire data for this image?"),
        max_length=10,
        choices=REMOTE_OBSERVATORY_CHOICES,
        null=True,
        blank=True,
    )

    solar_system_main_subject = models.CharField(
        verbose_name=_("Main solar system subject"),
        help_text=_(
            "If the main subject of your image is a body in the solar system, please select which (or which type) it is."),
        null=True,
        blank=True,
        max_length=32,
        choices=SOLAR_SYSTEM_SUBJECT_CHOICES,
    )

    locations = models.ManyToManyField(
        'astrobin.Location',
        verbose_name=_("Locations"),
        help_text=_("Drag items from the right side to the left side, or click on the plus sign."),
        blank=True,
    )

    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Description"),
        help_text=_("HTML tags are allowed."),
    )

    description_bbcode = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Description"),
    )

    link = models.CharField(
        max_length=256,
        null=True,
        blank=True,
    )

    link_to_fits = models.CharField(
        max_length=256,
        null=True,
        blank=True,
    )

    image_file = models.ImageField(
        upload_to=image_upload_path,
        height_field='h',
        width_field='w',
        max_length=256,
        null=True,
    )

    video_file = models.FileField(
        upload_to=video_upload_path,
        max_length=256,
        null=True,
    )

    encoded_video_file = models.FileField(
        upload_to=video_upload_path,
        null=True,
        max_length=256,
    )

    encoding_error = models.TextField(
        blank=True,
        null=True,
        editable=False,
    )

    loop_video = models.NullBooleanField(
        default=None,
    )

    uncompressed_source_file = models.FileField(
        upload_to=uncompressed_source_upload_path,
        validators=(FileValidator(allowed_extensions=(settings.ALLOWED_UNCOMPRESSED_SOURCE_EXTENSIONS)),),
        verbose_name=_("Uncompressed source (max 100 MB)"),
        help_text=_(
            "You can store the final processed image that came out of your favorite image editor (e.g. PixInsight, "
            "Adobe Photoshop, etc) here on AstroBin, for archival purposes. This file is stored privately and only you "
            "will have access to it."),
        max_length=256,
        null=True,
    )

    square_cropping = ImageRatioField(
        'image_file',
        '130x130',
        verbose_name=_("Gallery thumbnail"),
        help_text=_("Select an area of the image to be used as thumbnail in your gallery.")
    )

    sharpen_thumbnails = models.BooleanField(
        default=False,
        verbose_name=_('Sharpen thumbnails'),
        help_text=_(
            'If selected, AstroBin will use a resizing algorithm that slightly sharpens all sizes of the image except '
            'the full size version.')
        ,
    )

    full_size_display_limitation = models.CharField(
        max_length=16,
        null=True,
        blank=True,
        default=FullSizeDisplayLimitation.EVERYBODY,
        verbose_name=_('Allow full-size display'),
        help_text=_('Specify what user groups are allowed to view this image at its full size.'),
        choices=FULL_SIZE_DISPLAY_LIMITATION_CHOICES
    )

    download_limitation = models.CharField(
        max_length=16,
        null=True,
        blank=True,
        choices=DOWNLOAD_LIMITATION_CHOICES,
        default=DownloadLimitation.ME_ONLY,
        verbose_name=_("Display download menu"),
        help_text=_(
            "Please note: even if you allow everyone to access download options, only you will be able to download the "
            "originally uploaded file."
        ),
    )

    uploaded = models.DateTimeField(editable=False, auto_now_add=True)
    published = models.DateTimeField(editable=False, null=True, blank=True)
    updated = models.DateTimeField(editable=False, auto_now=True, null=True, blank=True)
    submitted_for_iotd_tp_consideration = models.DateTimeField(editable=False, null=True, blank=True)
    disqualified_from_iotd_tp = models.DateTimeField(editable=False, null=True, blank=True)

    designated_iotd_submitters = models.ManyToManyField(
        User,
        related_name='designated_images_as_submitter',
        editable=False
    )

    designated_iotd_reviewers = models.ManyToManyField(
        User,
        related_name='designated_images_as_reviewer',
        editable=False
    )

    # For likes, bookmarks, and perhaps more.
    toggleproperties = GenericRelation(ToggleProperty)

    # Counts
    like_count = models.PositiveIntegerField(editable=False, default=0)
    bookmark_count = models.PositiveIntegerField(editable=False, default=0)
    comment_count = models.PositiveIntegerField(editable=False, default=0)

    watermark_text = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        verbose_name="Text",
    )

    watermark = models.BooleanField(
        default=False,
        verbose_name=_("Apply watermark to image"),
    )

    watermark_position = models.IntegerField(
        verbose_name=_("Position"),
        default=0,
        choices=WATERMARK_POSITION_CHOICES,
    )

    watermark_size = models.CharField(
        max_length=1,
        choices=WATERMARK_SIZE_CHOICES,
        default='M',
        verbose_name=_("Size"),
        help_text=_("The final font size will depend on how long your watermark is."),
    )

    watermark_opacity = models.IntegerField(
        default=10,
    )

    ####################################################################################################################
    # LEGACY GEAR
    ####################################################################################################################
    imaging_telescopes = models.ManyToManyField(
        Telescope,
        blank=True,
        related_name='images_using_for_imaging',
        verbose_name=_("Imaging telescopes or lenses")
    )

    guiding_telescopes = models.ManyToManyField(
        Telescope,
        blank=True,
        related_name='images_using_for_guiding',
        verbose_name=_("Guiding telescopes or lenses")
    )

    mounts = models.ManyToManyField(
        Mount,
        blank=True,
        related_name='images_using',
        verbose_name=_("Mounts")
    )

    imaging_cameras = models.ManyToManyField(
        Camera,
        blank=True,
        related_name='images_using_for_imaging',
        verbose_name=_("Imaging cameras")
    )

    guiding_cameras = models.ManyToManyField(
        Camera,
        blank=True,
        related_name='images_using_for_guiding',
        verbose_name=_("Guiding cameras")
    )

    focal_reducers = models.ManyToManyField(
        FocalReducer,
        blank=True,
        related_name='images_using',
        verbose_name=_("Focal reducers")
    )

    software = models.ManyToManyField(
        Software,
        blank=True,
        related_name='images_using',
        verbose_name=_("Software")
    )

    filters = models.ManyToManyField(
        Filter,
        blank=True,
        related_name='images_using',
        verbose_name=_("Filters")
    )

    accessories = models.ManyToManyField(
        Accessory,
        blank=True,
        related_name='images_using',
        verbose_name=_("Accessories")
    )
    ####################################################################################################################

    ####################################################################################################################
    # NEW EQUIPMENT DATABASE
    ####################################################################################################################
    imaging_telescopes_2 = models.ManyToManyField(
        TelescopeV2,
        blank=True,
        related_name='images_using_for_imaging',
        verbose_name=_("Imaging telescopes or lenses")
    )

    guiding_telescopes_2 = models.ManyToManyField(
        TelescopeV2,
        blank=True,
        related_name='images_using_for_guiding',
        verbose_name=_("Guiding telescopes or lenses")
    )

    mounts_2 = models.ManyToManyField(
        MountV2,
        blank=True,
        related_name='images_using',
        verbose_name=_("Mounts")
    )

    imaging_cameras_2 = models.ManyToManyField(
        CameraV2,
        blank=True,
        related_name='images_using_for_imaging',
        verbose_name=_("Imaging cameras")
    )

    guiding_cameras_2 = models.ManyToManyField(
        CameraV2,
        blank=True,
        related_name='images_using_for_guiding',
        verbose_name=_("Guiding cameras")
    )

    software_2 = models.ManyToManyField(
        SoftwareV2,
        blank=True,
        related_name='images_using',
        verbose_name=_("Software")
    )

    filters_2 = models.ManyToManyField(
        FilterV2,
        blank=True,
        related_name='images_using',
        verbose_name=_("Filters")
    )

    accessories_2 = models.ManyToManyField(
        AccessoryV2,
        blank=True,
        related_name='images_using',
        verbose_name=_("Accessories")
    )
    ####################################################################################################################

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    pending_collaborators = models.ManyToManyField(User, blank=True, related_name='images_as_pending_collaborator')
    collaborators = models.ManyToManyField(User, blank=True, related_name='images_as_collaborator')

    plot_is_overlay = models.BooleanField(editable=False, default=False)
    is_wip = models.BooleanField(default=False)

    # Size of the image in bytes
    size = models.PositiveIntegerField(editable=False, default=0)

    w = models.IntegerField(editable=False, default=0)
    h = models.IntegerField(editable=False, default=0)
    animated = models.BooleanField(editable=False, default=False)

    license = models.CharField(
        max_length=40,
        choices=LICENSE_CHOICES,
        default=License.ALL_RIGHTS_RESERVED,
        verbose_name=_("License"),
    )

    is_final = models.BooleanField(
        editable=False,
        default=True
    )

    allow_comments = models.BooleanField(
        verbose_name=_("Allow comments"),
        default=True,
    )

    nested_comments = GenericRelation(NestedComment, related_query_name='image')

    mouse_hover_image = models.CharField(
        null=True,
        blank=True,
        default=MouseHoverImage.SOLUTION,
        max_length=16,
    )

    moderator_decision = models.PositiveIntegerField(
        editable=False,
        default=ModeratorDecision.UNDECIDED,
    )

    moderated_when = models.DateTimeField(
        editable=False,
        null=True,
        auto_now_add=False,
        default=None,
    )

    moderated_by = models.ForeignKey(
        User,
        editable=False,
        null=True,
        related_name='images_moderated',
        on_delete=models.SET_NULL,
    )

    skip_notifications = models.BooleanField(
        default=False,
        verbose_name=_("Skip notifications"),
        help_text=_("Do not notify your followers about this image upload.")
    )

    skip_activity_stream = models.NullBooleanField(
        null=True,
        blank=True,
        default=None,
        verbose_name=_("Skip activity stream"),
        help_text=_("Do not create an entry on the front page's activity stream for this event.")
    )

    # To prevent expensive queries, we store the constellation here. It gets update with a signal every time the
    # Solution is saved.
    constellation = models.CharField(
        max_length=3,
        null=True,
        blank=True,
    )

    # To prevent a billion cache requests when looking at user galleries, we store the final gallery thumbnail here.
    final_gallery_thumbnail = models.CharField(max_length=512, null=True, blank=True)

    class Meta:
        app_label = 'astrobin'
        ordering = ('-uploaded', '-id')

    objects = PublicImagesManager()
    objects_plain = PublicImagesPlainManager()
    objects_including_wip = ImagesManager()
    objects_including_wip_plain = ImagesPlainManager()
    wip = WipImagesManager()
    uploads_in_progress = UploadsInProgressImagesManager()

    def __str__(self):
        return self.title if self.title is not None else _("(no title)")

    def get_id(self):
        return self.hash if self.hash else self.pk

    def get_absolute_url(self, revision='final', size='regular'):
        if revision == 'final':
            if not self.is_final:
                r = self.revisions.filter(is_final=True)
                if r:
                    revision = r[0].label

        url = '/'
        if size == 'full':
            url += 'full/'

        url += '%s/' % (self.hash if self.hash else self.pk)

        if revision != 'final':
            url += '%s/' % revision

        return url

    def liked_by(self):
        key = "Image.%d.liked_by" % self.pk
        val = cache.get(key)
        if val is None:
            user_pks = ToggleProperty.objects \
                .toggleproperties_for_object("like", self) \
                .select_related('user') \
                .values_list('user', flat=True)
            val = [profile.user for profile in UserProfile.objects.filter(user__pk__in=user_pks)]
            cache.set(key, val, 300)
        return val

    def bookmarked_by(self):
        key = "Image.%d.bookmarked_by" % self.pk
        val = cache.get(key)
        if val is None:
            user_pks = ToggleProperty.objects \
                .toggleproperties_for_object("bookmark", self) \
                .select_related('user') \
                .values_list('user', flat=True)
            val = [profile.user for profile in UserProfile.objects.filter(user__pk__in=user_pks)]
            cache.set(key, val, 300)
        return val

    def comments_by_distinct_users(self):
        from nested_comments.models import NestedComment
        key = "Image.%d.comments_by_distinct_users" % self.pk
        val = cache.get(key)
        if val is None:
            user_pks = NestedComment.objects.filter(
                deleted=False,
                content_type__app_label='astrobin',
                content_type__model='image',
                object_id=self.id) \
                .select_related('author') \
                .values_list('author', flat=True) \
                .distinct()
            val = len(user_pks)
            cache.set(key, val, 300)
        return val

    def commented_by(self):
        from nested_comments.models import NestedComment
        key = "Image.%d.commented_by" % self.pk
        val = cache.get(key)
        if val is None:
            user_pks = NestedComment.objects.filter(
                deleted=False,
                content_type__app_label='astrobin',
                content_type__model='image',
                object_id=self.id) \
                .select_related('author') \
                .values_list('author', flat=True)
            val = [profile.user for profile in UserProfile.objects.filter(user__pk__in=user_pks)]
            cache.set(key, val, 300)
        return val

    def get_thumbnail_field(self, revision_label):
        # We default to the original upload
        field = self.image_file

        if revision_label == '0':
            pass
        elif revision_label == 'final':
            for r in self.revisions.all():
                if r.is_final:
                    field = r.image_file
        else:
            # We have some label
            try:
                r = ImageRevision.objects.get(image=self, label=revision_label)
                field = r.image_file
            except ImageRevision.DoesNotExist:
                pass

        return field

    def get_thumbnail_options(self, alias, revision_label, thumbnail_settings):
        from astrobin_apps_images.services import ImageService

        options = dict(settings.THUMBNAIL_ALIASES[''][alias].copy(), **thumbnail_settings)

        crop_box = ImageService(self).get_crop_box(alias, revision_label=revision_label)
        if crop_box and alias not in ('real', 'real_inverted'):
            options['box'] = crop_box
            options['crop'] = True

        if self.watermark and 'watermark' in options:
            options['watermark_text'] = self.watermark_text
            options['watermark_position'] = self.watermark_position
            options['watermark_size'] = self.watermark_size
            options['watermark_opacity'] = self.watermark_opacity

        # Make sure this is in because easy-thumbnails adds it in same cases.
        options['subsampling'] = 2

        return options

    def thumbnail_raw(self, alias: str, revision_label: str, **kwargs) -> Optional[ThumbnailFile]:
        from easy_thumbnails.files import get_thumbnailer
        from astrobin.s3utils import OverwritingFileSystemStorage

        thumbnail_settings = kwargs.get('thumbnail_settings', {})

        if revision_label is None:
            revision_label = 'final'

        # Compatibility
        if alias in ('revision', 'runnerup'):
            alias = 'gallery'

        field = self.get_thumbnail_field(revision_label)
        if not field.name:
            return None

        Image._normalize_field_name(field)

        try:
            if settings.AWS_S3_ENABLED:
                thumbnailer = get_thumbnailer(field.file, field.name)
            else:
                storage = OverwritingFileSystemStorage(location=os.path.join(settings.UPLOADS_DIRECTORY))
                thumbnailer = get_thumbnailer(storage, field.name)

            thumb = thumbnailer.get_thumbnail(self.get_thumbnail_options(alias, revision_label, thumbnail_settings))
        except Exception as e:
            log.error("Image %d: unable to generate thumbnail: %s." % (self.id, str(e)))
            return None

        return thumb

    def thumbnail_cache_key(self, field: FileField, alias: str, revision_label: str) -> str:
        app_model = "{0}.{1}".format(
            self._meta.app_label,
            self._meta.object_name).lower()
        cache_key = 'easy_thumb_alias_cache_%s.%s_%s_%s_%s' % (
            app_model,
            unicodedata.normalize('NFKD', str(field)).encode('ascii', 'ignore'),
            alias,
            revision_label,
            self.square_cropping)

        from hashlib import sha256
        return sha256(cache_key.encode('utf-8')).hexdigest()

    def thumbnail(self, alias: str, revision_label: str, **kwargs) -> str:
        def normalize_url_security(url: str, thumbnail_settings: dict) -> str:
            insecure = 'insecure' in thumbnail_settings and thumbnail_settings['insecure']
            if insecure and url.startswith('https'):
                return url.replace('https', 'http', 1)

            return url

        from astrobin_apps_images.models import ThumbnailGroup
        from astrobin_apps_images.services import ImageService

        placeholder = static('astrobin/images/placeholder-gallery.jpg')

        thumbnail_settings = kwargs.pop('thumbnail_settings', {})
        sync = kwargs.pop('sync', False)

        # For compatibility:
        if alias in ('revision', 'runnerup'):
            alias = 'gallery'

        final_revision_label = ImageService(self).get_final_revision_label()
        if revision_label in (None, 'None', 'final', final_revision_label):
            if alias == 'gallery' and self.final_gallery_thumbnail:
                return normalize_url_security(self.final_gallery_thumbnail, thumbnail_settings)
            revision_label = final_revision_label

        field = self.get_thumbnail_field(revision_label)
        if not field.name or 'placeholder' in field.url:
            return placeholder

        Image._normalize_field_name(field)

        options = self.get_thumbnail_options(alias, revision_label, thumbnail_settings)

        cache_key = self.thumbnail_cache_key(field, alias, revision_label)

        # If this is an animated gif, let's just return the full size URL
        # because right now we can't thumbnail gifs preserving animation
        if kwargs.pop('animated', False) and alias in (
                'regular',
                'regular_sharpened',
                'regular_large',
                'regular_large_sharpened',
                'hd',
                'hd_sharpened',
                'hd_anonymized',
                'hd_anonymized_crop',
                'qhd',
                'qhd_sharpened',
                'qhd_anonymized',
                'real',
                'real_anonymized'
        ):
            url = settings.IMAGES_URL + field.name
            cache.set(cache_key + '_animated', url, 60 * 60 * 24)
            return normalize_url_security(url, thumbnail_settings)

        url = cache.get(cache_key)
        if url and 'ERROR' not in url:
            return normalize_url_security(url, thumbnail_settings)

        # Not found in cache, attempt to fetch from database
        try:
            thumbnails = self.thumbnails.get(revision=revision_label)
            url = getattr(thumbnails, alias)
            if url and 'ERROR' not in url:
                cache.set(cache_key, url, 60 * 60 * 24)
                return normalize_url_security(url, thumbnail_settings)
        except ThumbnailGroup.DoesNotExist:
            try:
                ThumbnailGroup.objects.create(image=self, revision=revision_label)
            except IntegrityError:
                # Race condition
                pass

        if sync:
            thumb = self.thumbnail_raw(alias, revision_label, thumbnail_settings=options)
            if thumb:
                ImageService(self).set_thumb(alias, revision_label, thumb.url)
                return thumb.url
            return placeholder

        # If we got down here, we don't have an url yet, so we start an asynchronous task and return a placeholder.
        task_id_cache_key = '%s.retrieve' % cache_key
        task_id = cache.get(task_id_cache_key)
        if task_id is None:
            from .tasks import retrieve_thumbnail
            result = retrieve_thumbnail.apply_async(args=(self.pk, alias, revision_label, options))
            cache.set(task_id_cache_key, result.task_id, 600)

            try:
                # Try again in case of eagerness.
                thumbnails = self.thumbnails.get(revision=revision_label)

                if thumbnails:
                    url = getattr(thumbnails, alias)
                    if url:
                        return url
            except ThumbnailGroup.DoesNotExist:
                pass
        else:
            AsyncResult(task_id)

        return placeholder

    def thumbnail_invalidate_real(self, field, revision_label, delete=True):
        from astrobin_apps_images.models import ThumbnailGroup

        for alias, thumbnail_settings in settings.THUMBNAIL_ALIASES[''].items():
            cache_key = self.thumbnail_cache_key(field, alias, revision_label)
            if cache.get(cache_key):
                cache.delete(cache_key)
                cache.delete('%s.retrieve' % cache_key)

        try:
            thumbnail_group = self.thumbnails.get(revision=revision_label)  # type: ThumbnailGroup
            all_urls: List[str] = [x for x in thumbnail_group.get_all_urls() if x and x.startswith('http')]

            if settings.AWS_S3_ENABLED:
                for url in all_urls:
                    s3 = boto3.client('s3')
                    s3.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=urlparse(url).path.strip('/'))

            self.thumbnails.get(revision=revision_label).delete()
        except ThumbnailGroup.DoesNotExist:
            pass

        Image.objects_including_wip.filter(pk=self.pk).update(
            final_gallery_thumbnail=None,
            updated=DateTimeService.now()
        )

    def thumbnail_invalidate(self, delete=True):
        return self.thumbnail_invalidate_real(self.image_file, '0', delete)

    def get_data_source(self):
        LOOKUP = {
            "BACKYARD": _("Backyard"),
            "TRAVELLER": _("Traveller"),
            "OWN_REMOTE": _("Own remote observatory"),
            "AMATEUR_HOSTING": _("Amateur hosting facility"),
            "PUBLIC_AMATEUR_DATA": _("Public amateur data"),
            "PRO_DATA": _("Professional, scientific grade data"),
            "MIX": _("Mix of multiple source"),
            "OTHER": _("Other"),
            "UNKNOWN": _("Unknown"),
            "UNSET": "None",
            None: None
        }

        return LOOKUP[self.data_source]

    def get_remote_source(self):
        for source in self.REMOTE_OBSERVATORY_CHOICES:
            if self.remote_source == source[0]:
                return source[1]

    def get_keyvaluetags(self):
        tags = self.keyvaluetags.all()

        if tags.count() == 0:
            return ""

        return '\r\n'.join([str(x) for x in self.keyvaluetags.all()])

    @staticmethod
    def _normalize_field_name(field):
        _, file_extension = os.path.splitext(field.name)

        if file_extension in settings.ALLOWED_IMAGE_EXTENSIONS and not field.name.startswith('images/'):
            field.name = 'images/' + field.name
        elif file_extension in settings.ALLOWED_VIDEO_EXTENSIONS and not field.name.startswith('videos/'):
            field.name = 'videos/' + field.name


class ImageEquipmentLog(models.Model):
    ADDED = 'ADDED'
    REMOVED = 'REMOVED'

    VERB_CHOICES = (
        (ADDED, 'Added'),
        (REMOVED, 'Removed'),
    )

    image = models.ForeignKey(Image, on_delete=models.CASCADE)
    equipment_item_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    equipment_item_object_id = models.PositiveIntegerField()
    equipment_item = GenericForeignKey('equipment_item_content_type', 'equipment_item_object_id')
    date = models.DateTimeField(auto_now_add=True)
    verb = models.CharField(max_length=32, choices=VERB_CHOICES)

    class Meta:
        app_label = 'astrobin'
        ordering = ('-date',)
        indexes = [
            models.Index(fields=['equipment_item_content_type', 'equipment_item_object_id', 'image', 'date']),
            models.Index(fields=['image']),
        ]

class ImageRevision(HasSolutionMixin, SafeDeleteModel):
    image = models.ForeignKey(
        Image,
        related_name='revisions',
        on_delete=models.CASCADE,
    )

    solutions = GenericRelation(Solution)

    corrupted = models.BooleanField(
        default=False
    )

    recovered = models.DateTimeField(
        null=True,
        blank=True
    )

    recovery_ignored = models.DateTimeField(
        null=True,
        blank=True
    )

    image_file = models.ImageField(
        upload_to=image_upload_path,
        height_field='h',
        width_field='w',
        null=True,
        max_length=256,
    )

    video_file = models.FileField(
        upload_to=video_upload_path,
        null=True,
        max_length=256,
    )

    encoded_video_file = models.FileField(
        upload_to=video_upload_path,
        null=True,
        max_length=256,
    )

    encoding_error = models.TextField(
        blank=True,
        null=True,
        editable=False,
    )

    loop_video = models.NullBooleanField(
        default=None,
    )

    uploader_in_progress = models.NullBooleanField(
        default=None,
        editable=False
    )

    uploader_name = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        editable=False,
    )

    uploader_upload_length = models.PositiveIntegerField(
        null=True,
        blank=True,
        editable=False,
    )

    uploader_offset = models.PositiveIntegerField(
        null=True,
        blank=True,
        editable=False,
    )

    uploader_expires = models.DateTimeField(
        null=True,
        blank=True,
        editable=False,
    )

    uploader_metadata = models.TextField(
        null=True,
        blank=True,
        editable=False,
    )

    uploader_temporary_file_path = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        editable=False,
    )

    square_cropping = ImageRatioField(
        'image_file',
        '130x130',
        verbose_name=_("Gallery thumbnail"),
        help_text=_("Select an area of the image to be used as thumbnail in your gallery.")
    )

    title = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        verbose_name=_("Title"),
        help_text=_("The revision's title will be shown as an addendum to the original image's title.")
    )

    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Description"),
        help_text=_("HTML tags are allowed."),
    )

    mouse_hover_image = models.CharField(
        null=True,
        blank=True,
        default=MouseHoverImage.SOLUTION,
        max_length=16,
    )

    skip_notifications = models.NullBooleanField(
        null=True,
        blank=True,
        default=None,
        verbose_name=_("Skip notifications"),
        help_text=_("Do not notify your followers about this revision.")
    )

    skip_activity_stream = models.NullBooleanField(
        null=True,
        blank=True,
        default=None,
        verbose_name=_("Skip activity stream"),
        help_text=_("Do not create an entry on the front page's activity stream for this event.")
    )

    uploaded = models.DateTimeField(editable=False, auto_now_add=True)

    # Size of the image in bytes
    size = models.PositiveIntegerField(editable=False, default=0)

    w = models.IntegerField(editable=False, default=0)
    h = models.IntegerField(editable=False, default=0)

    is_final = models.BooleanField(
        editable=False,
        default=False
    )

    label = models.CharField(
        max_length=2,
        editable=False)

    class Meta:
        app_label = 'astrobin'
        ordering = ('uploaded', '-id')
        unique_together = ('image', 'label')

    objects = ImageRevisionsManager()
    uploads_in_progress = UploadsInProgressImageRevisionsManager()

    def __str__(self):
        return self.image.title

    def save(self, *args, **kwargs):
        if self.w == 0 or self.h == 0:
            try:
                self.w, self.h = get_image_dimensions(self.image_file.file)
            except Exception as e:
                log.warning("ImageRevision.save: unable to get image dimensions for %d: %s" % (
                    self.pk if self.pk else 0, str(e)))
                pass

        if self.w == self.image.w and self.h == self.image.h and not self.square_cropping:
            self.square_cropping = self.image.square_cropping

        if self.is_final:
            if self.image.is_final:
                self.image.is_final = False
                self.image.save(keep_deleted=True)
            from astrobin_apps_images.services import ImageService
            ImageService(self.image).get_revisions(True) \
                .filter(is_final=True) \
                .exclude(label=self.label) \
                .update(is_final=False)

        super(ImageRevision, self).save(*args, **kwargs)
        Image.all_objects.filter(pk=self.image.pk).update(updated=timezone.now())
        UserProfile.all_objects.filter(pk=self.image.user.pk).update(updated=timezone.now())

        if self.image.solution and self.image.solution.settings:
            solution, created = Solution.objects.get_or_create(
                content_type=ContentType.objects.get_for_model(ImageRevision),
                object_id=self.pk)
            if created:
                settings = self.image.solution.settings  # type: PlateSolvingSettings
                settings.pk = None
                settings.save()
                solution.settings = settings

                if self.image.solution.advanced_settings:
                    advanced_settings = self.image.solution.advanced_settings  # type: PlateSolvingAdvancedSettings
                    advanced_settings.pk = None
                    advanced_settings.save()
                    solution.advanced_settings = advanced_settings

                solution.save()

    def get_absolute_url(self, revision='nd', size='regular'):
        # We can ignore the revision argument of course
        if size == 'full':
            return '/%s/%s/full/' % (self.image.get_id(), self.label)

        return '/%s/%s/' % (self.image.get_id(), self.label)

    def thumbnail_raw(self, alias, **kwargs):
        return self.image.thumbnail_raw(alias, self.label, **kwargs)

    def thumbnail(self, alias, **kwargs):
        return self.image.thumbnail(alias, self.label, **kwargs)

    def thumbnail_invalidate(self, delete=True):
        return self.image.thumbnail_invalidate_real(self.image_file, self.label, delete)


class Collection(models.Model):
    date_created = models.DateField(
        null=False,
        blank=False,
        auto_now_add=True,
        editable=False,
    )

    date_updated = models.DateField(
        null=False,
        blank=False,
        auto_now=True,
        editable=False,
    )

    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='children',
        on_delete=models.CASCADE,
        verbose_name=_("Parent collection"),
        help_text=_("If you want to create a nested collection, select the parent collection here."),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    name = models.CharField(
        max_length=256,
        null=False,
        blank=False,
        verbose_name=_("Name"),
    )

    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Description"),
    )

    images = models.ManyToManyField(
        Image,
        verbose_name=_("Images"),
        related_name='collections',
        blank=True,
    )

    cover = models.ForeignKey(
        Image,
        null=True,
        blank=True,
        verbose_name=_("Cover image"),
        on_delete=models.SET_NULL,
    )

    order_by_tag = models.CharField(
        null=True,
        blank=True,
        max_length=255,
        verbose_name=_("Order by image tag")
    )

    class Meta:
        app_label = 'astrobin'
        unique_together = ('user', 'name')
        ordering = ['name']

    def __str__(self):
        return self.name


class Acquisition(models.Model):
    date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date"),
        help_text=_("Please use the following format: yyyy-mm-dd."),
    )

    image = models.ForeignKey(
        Image,
        verbose_name=_("Image"),
        on_delete=models.CASCADE,
    )

    class Meta:
        app_label = 'astrobin'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        Image.objects_including_wip.filter(pk=self.image.pk).update(updated=DateTimeService.now())


class DeepSky_Acquisition(Acquisition):
    BINNING_CHOICES = (
        (1, '1x1'),
        (2, '2x2'),
        (3, '3x3'),
        (4, '4x4'),
    )

    BORTLE_CHOICES = (
        (1, _("1 - Excellent dark-site sky (BLACK)")),
        (2, _("2 - Typical truly dark site (GRAY)")),
        (3, _("3 - Rural sky (BLUE)")),
        (4, _("4 - Rural/suburban transition (GREEN/YELLOW)")),
        (4.5, _("4.5 - Semi-Suburban/Transition sky (YELLOW)")),
        (5, _("5 - Suburban sky (ORANGE)")),
        (6, _("6 - Bright suburban sky (RED)")),
        (7, _("7 - Suburban/urban transition or Full Moon (RED)")),
        (8, _("8 - City sky (WHITE)")),
        (9, _("9 - Inner city sky (WHITE)")),
    )

    is_synthetic = models.BooleanField(
        _("Synthetic channel"),
        default=False,
    )

    filter = models.ForeignKey(
        Filter,
        null=True,
        blank=True,
        verbose_name=_("Filter"),
        on_delete=models.SET_NULL,
        related_name='deep_sky_acquisitions',
    )

    filter_2 = models.ForeignKey(
        FilterV2,
        null=True,
        blank=True,
        verbose_name=_("Filter"),
        on_delete=models.SET_NULL,
        related_name='deep_sky_acquisitions',
    )

    binning = models.IntegerField(
        null=True,
        blank=True,
        choices=BINNING_CHOICES,
        default=0,
        verbose_name=_("Binning"),
    )

    number = models.PositiveIntegerField(
        _("Number"),
        null=True,
        blank=True,
        help_text=_("The number of sub-frames."),
    )

    duration = models.DecimalField(
        _("Duration"),
        null=True,
        blank=True,
        max_digits=12,
        decimal_places=4,
        help_text=_("Duration of each sub-frame, in seconds."),
    )

    iso = models.PositiveIntegerField(
        _("ISO"),
        null=True,
        blank=True,
    )

    gain = models.DecimalField(
        _("Gain"),
        null=True,
        blank=True,
        max_digits=7,
        decimal_places=2,
    )

    f_number = models.DecimalField(
        _("f-number"),
        null=True,
        blank=True,
        max_digits=4,
        decimal_places=2,
        help_text=_(
            "If you used a camera lens, please specify the f-number (also known as f-ratio or f-stop) that you used "
            "for this acquisition session."
        )
    )

    sensor_cooling = models.IntegerField(
        _("Sensor cooling"),
        null=True,
        blank=True,
        help_text=_("The temperature of the chip. E.g.: -20."),
    )

    darks = models.PositiveIntegerField(
        _("Darks"),
        null=True,
        blank=True,
        help_text=_("The number of dark frames."),
    )

    flats = models.PositiveIntegerField(
        _("Flats"),
        null=True,
        blank=True,
        help_text=_("The number of flat frames."),
    )

    flat_darks = models.PositiveIntegerField(
        _("Flat darks"),
        null=True,
        blank=True,
        help_text=_("The number of flat dark frames."),
    )

    bias = models.PositiveIntegerField(
        _("Bias"),
        null=True,
        blank=True,
        help_text=_("The number of bias/offset frames."),
    )

    bortle = models.DecimalField(
        verbose_name=_("Bortle Dark-Sky Scale"),
        null=True,
        blank=True,
        max_digits=2,
        decimal_places=1,
        choices=BORTLE_CHOICES,
        help_text=_(
            "Quality of the sky according to <a href=\"http://en.wikipedia.org/wiki/Bortle_Dark-Sky_Scale\" target=\"_blank\">the Bortle Scale</a>."
        ),
    )

    mean_sqm = models.DecimalField(
        verbose_name=_("Mean mag/arcsec^2"),
        help_text=_("As measured with your Sky Quality Meter."),
        null=True,
        blank=True,
        max_digits=5,
        decimal_places=2,
    )

    mean_fwhm = models.DecimalField(
        _("Mean FWHM"),
        null=True,
        blank=True,
        max_digits=5,
        decimal_places=2,
    )

    temperature = models.DecimalField(
        _("Temperature"),
        null=True, blank=True,
        max_digits=5,
        decimal_places=2,
        help_text=_("Ambient temperature (in Centigrade degrees)."),
    )

    advanced = models.BooleanField(
        editable=False,
        default=False,
    )

    saved_on = models.DateTimeField(
        editable=False,
        auto_now=True,
        null=True,
    )

    class Meta:
        app_label = 'astrobin'
        ordering = ['saved_on']


class SolarSystem_Acquisition(Acquisition):
    frames = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Number of frames"),
        help_text=_("The total number of frames you have stacked."),
    )

    fps = models.DecimalField(
        verbose_name=_("FPS"),
        help_text=_("Frames per second."),
        max_digits=12,
        decimal_places=5,
        null=True,
        blank=True,
    )

    exposure_per_frame = models.DecimalField(
        verbose_name=_("Exposure per frame") + " (ms)",
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
    )

    focal_length = models.IntegerField(
        verbose_name=_("Focal length"),
        help_text=_("The focal length of the whole optical train, including barlow lenses or other components."),
        null=True,
        blank=True,
    )

    iso = models.PositiveIntegerField(
        "ISO",
        null=True,
        blank=True,
    )

    gain = models.DecimalField(
        "Gain",
        null=True,
        blank=True,
        max_digits=7,
        decimal_places=2,
    )

    cmi = models.DecimalField(
        verbose_name=_("CMI"),
        help_text=_("Latitude of the first Central Meridian."),
        null=True,
        blank=True,
        max_digits=5,
        decimal_places=2,
    )

    cmii = models.DecimalField(
        verbose_name=_("CMII"),
        help_text=_("Latitude of the second Central Meridian."),
        null=True,
        blank=True,
        max_digits=5,
        decimal_places=2,
    )

    cmiii = models.DecimalField(
        verbose_name=_("CMIII"),
        help_text=_("Latitude of the third Central Meridian."),
        null=True,
        blank=True,
        max_digits=5,
        decimal_places=2,
    )

    seeing = models.IntegerField(
        verbose_name=_("Seeing"),
        help_text=_("Your estimation of the seeing, on a scale from 1 to 5. Larger is better."),
        null=True,
        blank=True,
    )

    transparency = models.IntegerField(
        verbose_name=_("Transparency"),
        help_text=_("Your estimation of the transparency, on a scale from 1 to 10. Larger is better."),
        null=True,
        blank=True,
    )

    time = models.CharField(
        verbose_name=_("Time"),
        help_text=_("Please use the following format: hh:mm."),
        null=True,
        blank=True,
        max_length=5,
    )

    class Meta:
        app_label = 'astrobin'


class Request(models.Model):
    from_user = models.ForeignKey(User, editable=False, related_name='requester', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, editable=False, related_name='requestee', on_delete=models.CASCADE)
    fulfilled = models.BooleanField()
    message = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)

    objects = InheritanceManager()

    def __str__(self):
        return '%s %s: %s' % (_('Request from'), self.from_user.username, self.message)

    def get_absolute_url(self):
        return '/requests/detail/' + str(self.id) + '/'

    class Meta:
        app_label = 'astrobin'
        ordering = ['-created']


class ImageRequest(Request):
    TYPE_CHOICES = (
        ('INFO', _('Additional information')),
        ('FITS', _('TIFF/FITS')),
        ('HIRES', _('Higher resolution')),
    )

    image = models.ForeignKey(Image, editable=False, on_delete=models.CASCADE)
    type = models.CharField(max_length=8, choices=TYPE_CHOICES)


class UserProfile(SafeDeleteModel):
    GEAR_CLASS_LOOKUP = {
        'telescopes': Telescope,
        'mounts': Mount,
        'cameras': Camera,
        'focal_reducers': FocalReducer,
        'software': Software,
        'filters': Filter,
        'accessories': Accessory,
    }

    GEAR_ATTR_LOOKUP = {
        'Telescope': 'telescopes',
        'Camera': 'cameras',
        'Mount': 'mounts',
        'FocalReducer': 'focal_reducers',
        'Software': 'software',
        'Filter': 'filters',
        'Accessory': 'accessories',
    }

    DELETE_REASON_NOT_ACTIVE = 'NOT_ACTIVE'
    DELETE_REASON_DID_NOT_MEET_EXPECTATIONS = 'DID_NOT_MEET_EXPECTATIONS'
    DELETE_REASON_DOESNT_WORKE = 'DOESNT_WORK'
    DELETE_REASON_TOO_EXPENSIVE = 'TOO_EXPENSIVE'
    DELETE_REASON_PREFER_NOT_TO_SAY = 'PREFER_NOT_TO_SAY'
    DELETE_REASON_OTHER = 'OTHER'
    DELETE_REASON_IMAGE_SPAM = 'IMAGE_SPAM'
    DELETE_REASON_FORUM_SPAM = 'FORUM_SPAM'
    DELETE_REASON_BANNED = 'BANNED'

    DELETE_REASON_CHOICES = (
        (DELETE_REASON_NOT_ACTIVE, _('I am no longer active in astrophotography')),
        (DELETE_REASON_DID_NOT_MEET_EXPECTATIONS, _('This website did not meet my expectations')),
        (DELETE_REASON_DOESNT_WORKE, _('Something on this website doesn\'t work for me')),
        (DELETE_REASON_TOO_EXPENSIVE, _('The paid subscriptions are too expensive')),
        (DELETE_REASON_PREFER_NOT_TO_SAY, _('I prefer not to say')),
        (DELETE_REASON_OTHER, _('Other')),
    )

    SKILL_LEVEL_NA = 'NA'
    SKILL_LEVEL_BEGINNER = 'BEGINNER'
    SKILL_LEVEL_INTERMEDIATE = 'INTERMEDIATE'
    SKILL_LEVEL_ADVANCED = 'ADVANCED'
    SKILL_LEVEL_PROFESSIONAL = 'PROFESSIONAL'

    SKILL_LEVEL_NA_TITLE = _('n/a')
    SKILL_LEVEL_BEGINNER_TITLE = _("Beginner")
    SKILL_LEVEL_INTERMEDIATE_TITLE = _('Intermediate')
    SKILL_LEVEL_ADVANCED_TITLE = _('Advanced')
    SKILL_LEVEL_PROFESSIONAL_TITLE = _('Professional')

    SKILL_LEVEL_NA_DESCRIPTION = \
        _('I don\'t define myself as an astrophotographer at this time.')
    SKILL_LEVEL_BEGINNER_DESCRIPTION = \
        _('I started out recently and I\'m still getting familiar with the hobby.')
    SKILL_LEVEL_INTERMEDIATE_DESCRIPTION =\
        _('I have been doing astrophotography for a while and wouldn\'t classify myself as a beginner anymore.')
    SKILL_LEVEL_ADVANCED_DESCRIPTION = \
        _('I developed a comprehensive set of skills and master most aspects of astrophotography.')
    SKILL_LEVEL_PROFESSIONAL_DESCRIPTION = \
        _('Astrophotography is my profession or part of my profession.')

    SKILL_LEVEL_CHOICES = (
        (SKILL_LEVEL_NA, f'{SKILL_LEVEL_NA_TITLE}///{SKILL_LEVEL_NA_DESCRIPTION}'),
        (SKILL_LEVEL_BEGINNER, f'{SKILL_LEVEL_BEGINNER_TITLE}///{SKILL_LEVEL_BEGINNER_DESCRIPTION}'),
        (SKILL_LEVEL_INTERMEDIATE, f'{SKILL_LEVEL_INTERMEDIATE_TITLE}///{SKILL_LEVEL_INTERMEDIATE_DESCRIPTION}'),
        (SKILL_LEVEL_ADVANCED, f'{SKILL_LEVEL_ADVANCED_TITLE}///{SKILL_LEVEL_ADVANCED_DESCRIPTION}'),
        (SKILL_LEVEL_PROFESSIONAL, f'{SKILL_LEVEL_PROFESSIONAL_TITLE}///{SKILL_LEVEL_PROFESSIONAL_DESCRIPTION}'),
    )

    user = models.OneToOneField(User, editable=False, on_delete=models.CASCADE)

    updated = models.DateTimeField(
        editable=False,
        auto_now=True,
        null=True,
        blank=True,
    )

    # Update this field every time anything changes with the user's notifications, such as:
    # - A new notification is created
    # - A notification is marked as read/unread
    # - A notification is deleted
    # - A notification is updated
    #
    # This field is using for "last-modified" caching purposes.
    last_notification_update = models.DateTimeField(
        editable=False,
        null=True,
        blank=True,
    )

    suspended = models.DateTimeField(
        verbose_name=_('Suspended'),
        null=True,
        blank=True,
    )

    suspension_reason = models.CharField(
        verbose_name=_('Suspension reason'),
        null=True,
        blank=True,
        max_length=1024,
    )

    last_seen = models.DateTimeField(
        editable=False,
        null=True,
        blank=True,
    )

    last_seen_in_country = models.CharField(
        editable=False,
        null=True,
        blank=True,
        max_length=2
    )

    signup_country = models.CharField(
        editable=False,
        null=True,
        blank=True,
        max_length=2
    )

    display_member_since = models.BooleanField(
        default=True,
        verbose_name=_("Allow others to see when you created your AstroBin account"),
    )

    display_last_seen = models.BooleanField(
        default=True,
        verbose_name=_("Allow others to see when you last visited AstroBin"),
    )

    # Basic Information
    real_name = models.CharField(
        verbose_name=_("Real name"),
        help_text=_("If present, your real name will be used throughout the website."),
        max_length=128,
        null=True,
        blank=True,
    )

    website = models.CharField(
        verbose_name=_("Website"),
        max_length=128,
        null=True,
        blank=True,
    )

    job = models.CharField(
        verbose_name=_("Job"),
        max_length=128,
        null=True,
        blank=True,
    )

    hobbies = models.CharField(
        verbose_name=_("Hobbies"),
        max_length=128,
        null=True,
        blank=True,
        help_text=_("Do you have any hobbies other than astrophotography?"),
    )

    instagram_username = models.CharField(
        verbose_name=_("Instagram username"),
        help_text=_("If you provide this, AstroBin will tag you on Instagram if it's sharing an image of yours."),
        validators=[
            MinLengthValidator(4),
            MaxLengthValidator(31),
            RegexValidator(
                '^@[\w](?!.*?\.{2})[\w.]{1,28}[\w]$',
                _('An Instagram username must be between 3 and 30 characters, start with an @ sign, and only '
                  'have letters, numbers, periods, and underlines.')
            )
        ],
        max_length=31,
        null=True,
        blank=True
    )

    about = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("About you"),
        help_text=_("Write something about yourself. HTML tags are allowed."),
    )

    shadow_bans = models.ManyToManyField(
        "self",
        symmetrical=False
    )

    delete_reason = models.CharField(
        choices=DELETE_REASON_CHOICES,
        max_length=32,
        null=True,
        blank=False,
        verbose_name=_("Delete reason"),
        help_text=_("Why are you deleting your AstroBin account?"),
    )

    delete_reason_other = models.CharField(
        max_length=512,
        null=True,
        blank=True,
        verbose_name=_("Other"),
        help_text=_("Please tell us why you are deleting your account (minimum 30 characters). Thanks!"),
    )

    # Counter for uploaded images.
    premium_counter = models.PositiveIntegerField(
        default=0,
        editable=False
    )

    premium_offer = models.CharField(
        max_length=32,
        default=None,
        null=True,
        blank=True,
        editable=False,
    )

    premium_offer_expiration = models.DateTimeField(
        editable=False,
        null=True
    )

    premium_offer_sent = models.DateTimeField(
        editable=False,
        null=True
    )

    # Avatar
    avatar = models.CharField(max_length=64, editable=False, null=True, blank=True)

    exclude_from_competitions = models.BooleanField(
        default=False,
        verbose_name=_("I want to be excluded from competitions"),
        help_text=_(
            "Check this box to be excluded from competitions and contests, such as the Image of the Day, the Top "
            "Picks, other custom contests. This will remove you from the leaderboards and hide your Image Index "
            "and Contribution Index."),
    )

    auto_submit_to_iotd_tp_process = models.BooleanField(
        default=False,
        verbose_name=_("Automatically submit images for IOTD/TP consideration"),
        help_text=_(
            "Check this box to automatically submit your images for %(0)sIOTD/TP%(1)s consideration when they are "
            "published." % {'0': '<a href="https://welcome.astrobin.com/iotd" target="_blank">', '1': '</a>'}
        ),
    )

    agreed_to_iotd_tp_rules_and_guidelines = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("I agree to the IOTD/TP rules and guidelines"),
        help_text=_(
            "Check this box to confirm that you have read and agree to the IOTD/TP %(_0)srules%(_1)s and "
            "%(_2)sguidelines%(_3)s. Your images won't be submitted for IOTD/TP consideration if you don't agree." % {
                '_0': '<a href="https://welcome.astrobin.com/iotd#rules" target="_blank">',
                '_1': '</a>',
                '_2': '<a href="https://welcome.astrobin.com/iotd#photographer-guidelines" target="_blank">',
                '_3': '</a>'
            }
        )
    )

    agreed_to_marketplace_terms = models.DateTimeField(
        null=True,
        blank=True,
        editable=False,
    )

    banned_from_competitions = models.DateTimeField(
        null=True,
        blank=True,
        editable=False,
    )

    astrobin_index_bonus = models.SmallIntegerField(
        null=True,
        blank=True,
    )

    plate_solution_overlay_on_full_disabled = models.DateTimeField(
        null=True,
        blank=True,
    )

    open_notifications_in_new_tab = models.NullBooleanField(
        verbose_name=_("Open notifications in a new tab")
    )

    # Gear
    telescopes = models.ManyToManyField(
        Telescope,
        blank=True,
        verbose_name=_("Telescopes and lenses"),
        related_name='users_using',
    )

    mounts = models.ManyToManyField(
        Mount,
        blank=True,
        verbose_name=_("Mounts"),
        related_name='users_using',
    )

    cameras = models.ManyToManyField(
        Camera,
        blank=True,
        verbose_name=_("Cameras"),
        related_name='users_using',
    )

    focal_reducers = models.ManyToManyField(
        FocalReducer,
        blank=True,
        verbose_name=_("Focal reducers"),
        related_name='users_using',
    )

    software = models.ManyToManyField(
        Software,
        blank=True,
        verbose_name=_("Software"),
        related_name='users_using',
    )

    filters = models.ManyToManyField(
        Filter,
        blank=True,
        verbose_name=_("Filters"),
        related_name='users_using',
    )

    accessories = models.ManyToManyField(
        Accessory,
        blank=True,
        verbose_name=_("Accessories"),
        related_name='users_using',
    )

    default_frontpage_section = models.CharField(
        choices=(
            ('global', _("Global stream")),
            ('personal', _("Personal stream")),
            ('recent', _("All uploaded images")),
            ('followed', _("All images uploaded by people you follow")),
        ),
        default='global',
        max_length=16,
        null=False,
        verbose_name=_("Default front page view"),
    )

    default_gallery_sorting = models.SmallIntegerField(
        choices=(
            (0, _("Publication")),
            (1, _("Acquisition")),
            (2, _("Subject type")),
            (3, _("Year")),
            (4, _("Gear")),
            (5, _("Collections")),
            (6, _("Title")),
            (7, _("Constellation")),
        ),
        default=0,
        null=False,
        verbose_name=_("Default gallery sorting"),
    )

    display_wip_images_on_public_gallery = models.NullBooleanField(
        verbose_name=_("See your own Staging Area images on your gallery"),
        help_text=_("Select if you want your Staging Area images to appear on your own view of your gallery when you "
                    "are logged. If you choose 'No', your Staging Area images can be located via the 'View' menu entry "
                    "on your gallery page."),
    )

    default_license = models.CharField(
        max_length=40,
        choices=LICENSE_CHOICES,
        default=License.ALL_RIGHTS_RESERVED,
        verbose_name=_("Default license"),
        help_text=_("The license you select here is automatically applied to all your new images."),
    )

    accept_tos = models.BooleanField(
        editable=False,
        default=False
    )

    referral_code = models.CharField(
        max_length=32,
        null=True,
        blank=True,
    )

    receive_important_communications = models.BooleanField(
        default=False,
        verbose_name=_('I accept to receive rare important communications via email'),
        help_text=_(
            'This is highly recommended. These are very rare and contain information that you probably want to have.')
    )

    receive_newsletter = models.BooleanField(
        default=False,
        verbose_name=_('I accept to receive occasional newsletters via email'),
        help_text=_(
            'Newsletters do not have a fixed schedule, but in any case they are not sent out more often than once per month.')
    )

    receive_marketing_and_commercial_material = models.BooleanField(
        default=False,
        verbose_name=_('I accept to receive occasional marketing and commercial material via email'),
        help_text=_('These emails may contain offers, commercial news, and promotions from AstroBin or its partners.')
    )

    allow_astronomy_ads = models.BooleanField(
        default=True,
        verbose_name=_('Allow astronomy ads from our partners'),
        help_text=_('It would mean a lot if you chose to allow astronomy relevant, non intrusive ads on this website. '
                    'AstroBin is a small business run by a single person, and this kind of support would be amazing. '
                    'Thank you in advance!')
    )

    allow_retailer_integration = models.BooleanField(
        default=True,
        verbose_name=_('Allow retailer integration'),
        help_text=_('AstroBin may associate with retailers of astronomy and astrophotography equipment to enhance '
                    'the display of equipment items with links to sponsoring partners. The integration is subtle '
                    'and non intrusive, and it would help a lot if you didn\'t disable it. Thank you in advance!')
    )

    insufficiently_active_iotd_staff_member_reminders_sent = models.PositiveSmallIntegerField(
        default=0
    )

    inactive_account_reminder_sent = models.DateTimeField(
        null=True
    )

    never_activated_account_reminder_sent = models.DateTimeField(
        null=True
    )

    recovered_images_notice_sent = models.DateTimeField(
        null=True
    )

    detected_insecure_password = models.DateTimeField(
        null=True
    )

    # When a user has an insecure password, (see field above) we will send them a reminder to change it.
    # The link in the reminder will have this token in it. It's a way to make sure that the user is the one
    # who requested the password change.
    password_reset_token = models.CharField(
        max_length=32,
        null=True
    )

    # Preferences (notification preferences are stored in the django
    # notification model)
    language = models.CharField(
        max_length=8,
        null=True, blank=True,
        verbose_name=_("Language"),
        choices=LANGUAGE_CHOICES,
    )

    other_languages = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Other languages"),
        help_text=_("Other languages that you can read and write. This can be useful to other AstroBin members who "
                    "would like to communicate with you.")
    )

    skill_level = models.CharField(
        max_length=16,
        null=True,
        blank=True,
        verbose_name=_("Self-assessed skill level"),
        help_text=_("How would you categorize your current skills as an astrophotographer?"),
        choices=SKILL_LEVEL_CHOICES,
    )

    skill_level_updated = models.DateTimeField(
        editable=False,
        null=True,
        blank=True,
    )

    # One time notifications that won't disappear until marked as seen.

    seen_realname = models.BooleanField(
        default=False,
        editable=False,
    )

    seen_iotd_tp_is_explicit_submission = models.DateTimeField(
        null=True,
        blank=True,
    )

    # PYBBM fields
    signature = models.TextField(
        _('Signature'),
        blank=True,
        max_length=1024)

    signature_html = models.TextField(
        _('Signature HTML Version'),
        blank=True,
        max_length=1024 + 30)

    show_signatures = models.BooleanField(
        _('Show signatures'),
        blank=True,
        default=True)

    post_count = models.IntegerField(
        _('Post count'),
        blank=True,
        default=0)

    autosubscribe = models.BooleanField(
        _('Automatically subscribe'),
        help_text=_('Automatically subscribe to topics that you answer'),
        default=True)

    @property
    def receive_emails(self):
        return self.receive_forum_emails

    receive_forum_emails = models.BooleanField(
        _('Receive e-mails from subscribed forum topics'),
        default=True)

    image_recovery_process_started = models.DateTimeField(
        null=True,
        blank=True,
        editable=False,
    )

    image_recovery_process_completed = models.DateTimeField(
        null=True,
        blank=True,
        editable=False,
    )

    # Stripe data
    stripe_customer_id = models.CharField(
        editable=False,
        max_length=32,
        blank=True,
        null=True,
    )

    stripe_subscription_id = models.CharField(
        editable=False,
        max_length=32,
        blank=True,
        null=True,
    )

    # Computed fields

    contribution_index = models.DecimalField(
        editable=False,
        null=True,
        blank=True,
        max_digits=5,
        decimal_places=2,
    )

    image_index = models.DecimalField(
        editable=False,
        null=True,
        blank=True,
        max_digits=7,
        decimal_places=3,
    )

    followers_count = models.PositiveIntegerField(
        editable=False,
        default=0,
    )

    following_count = models.PositiveIntegerField(
        editable=False,
        default=0,
    )

    # Public images
    image_count = models.PositiveIntegerField(
        editable=False,
        default=0,
    )

    wip_image_count = models.PositiveIntegerField(
        editable=False,
        default=0,
    )

    deleted_image_count = models.PositiveIntegerField(
        editable=False,
        default=0,
    )

    def get_display_name(self) -> str:
        return self.real_name if self.real_name else str(self.user)

    def __str__(self) -> str:
        return self.get_display_name()

    def get_absolute_url(self) -> str:
        return reverse(
            'user_page', kwargs={'username': self.user.username}
        )

    def remove_gear(self, gear, gear_type):
        resolve = {
            'Telescope': 'telescopes',
            'Mount': 'mounts',
            'Camera': 'cameras',
            'FocalReducer': 'focal_reducers',
            'Software': 'software',
            'Filter': 'filters',
            'Accessory': 'accessories',
        }
        getattr(self, resolve[gear_type]).remove(gear)

    def get_scores(self):
        scores = {
            'user_scores_index': self.image_index,
            'user_scores_contribution_index': self.contribution_index,
            'user_scores_followers': self.followers_count,
        }

        return scores

    def is_moderator(self) -> bool:
        return UserService(self.user).is_in_group('content_moderators')

    def is_image_moderator(self) -> bool:
        return UserService(self.user).is_in_group('image_moderators')

    def is_iotd_staff(self) -> bool:
        return UserService(self.user).is_in_group(GroupName.IOTD_STAFF)

    def is_iotd_submitter(self) -> bool:
        return UserService(self.user).is_in_group(GroupName.IOTD_SUBMITTERS)

    def is_iotd_reviewer(self) -> bool:
        return UserService(self.user).is_in_group(GroupName.IOTD_REVIEWERS)

    def is_iotd_judge(self) -> bool:
        return UserService(self.user).is_in_group(GroupName.IOTD_JUDGES)

    class Meta:
        app_label = 'astrobin'


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        real_name = f'{(instance.first_name or "").strip()} {(instance.last_name or "").strip()}'.strip()
        profile, created = UserProfile.objects.get_or_create(user=instance, real_name=real_name)


post_save.connect(create_user_profile, sender=User)


class Location(models.Model):
    name = models.CharField(
        verbose_name=_("Name"),
        help_text=_("A descriptive name, e.g. 'Home observatory' or 'Mount Whitney'."),
        max_length=255,
        null=True,
        blank=False,
    )
    city = models.CharField(
        verbose_name=_("City"),
        help_text=_("If this location is not in a city, use the name of the closest city."),
        max_length=255,
        null=True,
        blank=False,
    )
    state = models.CharField(
        verbose_name=_("State or province"),
        max_length=255,
        null=True, blank=True,
    )
    country = CountryField(
        verbose_name=_("Country"),
        null=True,
        blank=True,
    )
    lat_deg = models.IntegerField(
        null=True,
        blank=False,
    )
    lat_min = models.IntegerField(
        null=True, blank=True
    )
    lat_sec = models.IntegerField(
        null=True, blank=True
    )
    lat_side = models.CharField(
        default='N',
        max_length=1,
        choices=(('N', _("North")), ('S', _("South"))),
        verbose_name=_('North or south'),
    )
    lon_deg = models.IntegerField(
        null=True,
        blank=False,
    )
    lon_min = models.IntegerField(
        null=True, blank=True
    )
    lon_sec = models.IntegerField(
        null=True, blank=True
    )
    lon_side = models.CharField(
        default='E',
        max_length=1,
        choices=(('E', _("East")), ('W', _("West"))),
        verbose_name=_('East or West'),
    )

    altitude = models.IntegerField(
        verbose_name=_("Altitude"),
        help_text=_("In meters."),
        null=True, blank=True)

    user = models.ForeignKey(
        UserProfile,
        editable=False,
        null=True,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return ', '.join([_f for _f in [
            self.name, self.city, self.state,
            str(get_country_name(self.country))
        ] if _f])

    class Meta:
        app_label = 'astrobin'


class App(models.Model):
    registrar = models.ForeignKey(
        User,
        editable=False,
        related_name='app_api_key',
        on_delete=models.SET(get_sentinel_user)
    )

    name = models.CharField(
        max_length=256,
        blank=False)

    description = models.TextField(
        null=True,
        blank=True)

    key = models.CharField(
        max_length=256,
        editable=False,
        blank=True,
        default='')

    secret = models.CharField(
        max_length=256,
        editable=False,
        blank=True,
        default='')

    active = models.BooleanField(
        editable=False,
        default=True)

    created = models.DateTimeField(
        editable=False,
        auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return "%s for %s" % (self.key, self.registrar)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        if not self.secret:
            self.secret = self.generate_key()

        return super(App, self).save(*args, **kwargs)

    def generate_key(self):
        # Get a random UUID.
        new_uuid = uuid.uuid4()
        # Hmac that beast.
        return hmac.new(b'key', str(new_uuid).encode('utf-8'), digestmod=sha1).hexdigest()


class AppApiKeyRequest(models.Model):
    registrar = models.ForeignKey(
        User,
        editable=False,
        related_name='app_api_key_request',
        on_delete=models.CASCADE)

    name = models.CharField(
        verbose_name=_("Name"),
        help_text=_("The name of the website or app that wishes to use the APIs."),
        max_length=256,
        blank=False,
        null=False
    )

    description = models.TextField(
        null=False,
        blank=False,
        verbose_name=_("Description"),
        help_text=_("Please explain the purpose of your application, and how you intend to use the API."),
        validators=[
            MinLengthValidator(100),
            MaxLengthValidator(500),
        ]
    )

    approved = models.BooleanField(
        editable=False,
        default=False,
    )

    created = models.DateTimeField(
        editable=False,
        auto_now_add=True,
    )

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return 'API request: %s' % self.name

    def save(self, *args, **kwargs):
        if self.pk is None:
            NotificationsService.email_superusers(
                'App API Key request from %s' % self.registrar.username,
                '%s/admin/astrobin/appapikeyrequest/' % settings.BASE_URL
            )

        return super(AppApiKeyRequest, self).save(*args, **kwargs)

    def approve(self):
        app, created = App.objects.get_or_create(
            registrar=self.registrar, name=self.name,
            description=self.description)

        self.approved = True
        self.save()

        if created:
            push_notification(
                [self.registrar], None, 'api_key_request_approved',
                {'api_docs_url': settings.BASE_URL + '/help/api/',
                 'api_keys_url': settings.BASE_URL + '/users/%s/apikeys/' % self.registrar.username,
                 'key': app.key,
                 'secret': app.secret})
        else:
            app.active = True

        app.save()


class ImageOfTheDay(models.Model):
    image = models.ForeignKey(
        Image,
        related_name='image_of_the_day',
        on_delete=models.CASCADE)

    date = models.DateField(
        auto_now_add=True)

    runnerup_1 = models.ForeignKey(
        Image,
        related_name='iotd_runnerup_1',
        null=True,
        on_delete=models.SET_NULL,
    )

    runnerup_2 = models.ForeignKey(
        Image,
        related_name='iotd_runnerup_2',
        null=True,
        on_delete=models.SET_NULL,
    )

    chosen_by = models.ForeignKey(
        User,
        related_name="iotds_chosen",
        null=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        ordering = ['-date']
        app_label = 'astrobin'

    def __str__(self):
        return "%s as an Image of the Day" % self.image.title


class ImageOfTheDayCandidate(models.Model):
    image = models.ForeignKey(
        Image,
        related_name='image_of_the_day_candidate',
        on_delete=models.CASCADE)

    date = models.DateField(
        auto_now_add=True)

    position = models.PositiveIntegerField()

    def save(self, *args, **kwargs):
        if self.image.user.userprofile.exclude_from_competitions:
            raise ValidationError("User is excluded from competitions")

        if self.image.user.userprofile.banned_from_competitions:
            raise ValidationError("User is banned from competitions")

        super(ImageOfTheDayCandidate, self).save(*args, **kwargs)

    class Meta:
        ordering = ['-date', 'position']
        app_label = 'astrobin'

    def __str__(self):
        return "%s as an Image of the Day Candidate" % self.image.title


class BroadcastEmail(models.Model):
    subject = models.CharField(max_length=200)
    created = models.DateTimeField(default=timezone.now)
    message = models.TextField()
    message_html = models.TextField(null=True)

    def __str__(self):
        return self.subject


class DataDownloadRequest(models.Model):
    STATUS_CHOICES = (
        ("PENDING", _("Pending")),
        ("PROCESSING", _("Processing")),
        ("READY", _("Ready")),
        ("ERROR", _("Error")),
        ("EXPIRED", _("Expired")),
    )

    user = models.ForeignKey(User, editable=False, on_delete=models.CASCADE)

    created = models.DateTimeField(
        null=False,
        blank=False,
        auto_now_add=True,
        editable=False,
    )

    zip_file = models.FileField(
        upload_to=data_download_upload_path,
        max_length=256,
        null=True,
    )

    file_size = models.BigIntegerField(
        null=True,
    )

    status = models.CharField(
        max_length=20,
        default="PENDING",
        choices=STATUS_CHOICES
    )

    def status_label(self):
        for i in self.STATUS_CHOICES:
            if self.status == i[0]:
                return i[1]

    class Meta:
        app_label = 'astrobin'
        ordering = ('-created',)


class PopupMessage(models.Model):
    title = models.CharField(
        max_length=256,
        null=False,
    )

    body = models.TextField(
        null=False,
    )

    created = models.DateTimeField(
        auto_now_add=True,
    )

    updated = models.DateTimeField(
        auto_now=True,
    )

    active = models.BooleanField(
        default=True,
    )

    def __str__(self):
        return self.title

    class Meta:
        ordering = ('-created',)
        indexes = [
            models.Index(fields=['active', '-created']),
        ]


class PopupMessageUserStatus(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )

    popup_message = models.ForeignKey(
        PopupMessage,
        on_delete=models.CASCADE,
    )

    seen = models.DateTimeField(
        null=True,
    )

    def __str__(self):
        return f'{self.user} - {self.popup_message}'

    class Meta:
        unique_together = ('user', 'popup_message',)
        ordering = ('-popup_message__created',)
        indexes = [
            models.Index(fields=['user', 'popup_message', 'seen']),
        ]
