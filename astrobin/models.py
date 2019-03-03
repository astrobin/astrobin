from __future__ import absolute_import

# Python
from datetime import date
from datetime import datetime
import hmac
import logging
import operator
import os
import unicodedata
import uuid

try:
    from hashlib import sha1
except ImportError:
    import sha
    sha1 = sha.sha

# Django
from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.db import models, IntegrityError
from django.db.models import Q
from django.db.models.signals import post_save
from django.template.defaultfilters import slugify
from django.utils import timezone
from django.utils import translation
from django.utils.translation import ugettext_lazy as _


try:
    # Django < 1.10
    from django.contrib.contenttypes.generic import GenericRelation
except ImportError:
    # Django >= 1.10
    from django.contrib.contenttypes.fields import GenericRelation

# Third party

from celery.result import AsyncResult
from model_utils.managers import InheritanceManager
from mptt.models import MPTTModel, TreeForeignKey
from reviews.models import Review
from safedelete.models import SafeDeleteModel
from tinymce import models as tinymce_models
from toggleproperties.models import ToggleProperty

try:
    # Django < 1.10
    from timezones.forms import PRETTY_TIMEZONE_CHOICES
except:
    # Django >= 1.10
    from timezones.zones import PRETTY_TIMEZONE_CHOICES

# AstroBin apps
from astrobin_apps_images.managers import ImagesManager, PublicImagesManager, WipImagesManager
from astrobin_apps_notifications.utils import push_notification
from astrobin_apps_platesolving.models import Solution
from nested_comments.models import NestedComment

# This app
from .fields import *
from .utils import user_is_paying


log = logging.getLogger('apps')


class HasSolutionMixin(object):
     @property
     def solution(self):
        ctype = ContentType.objects.get_for_model(self.__class__)

        try:
            solution = Solution.objects.get(content_type = ctype, object_id = self.id)
        except:
           return None

        return solution


def image_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    return "images/%d/%d/%s.%s" % (instance.user.id, date.today().year, uuid.uuid4(), ext)


LICENSE_CHOICES = (
    (0, _("None (All rights reserved)")),
    (1, _("Attribution-NonCommercial-ShareAlike Creative Commons")),
    (2, _("Attribution-NonCommercial Creative Commons")),
    (3, _("Attribution-NonCommercial-NoDerivs Creative Commons")),
    (4, _("Attribution Creative Commons")),
    (5, _("Attribution-ShareAlike Creative Commons")),
    (6, _("Attribution-NoDerivs Creative Commons")),
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
    ('pt-BR', _("Brazilian Portuguese")),
    ('el', _("Greek")),
    ('ru', _("Russian")),
    ('ar', _("Arabic")),
    ('ja', _("Japanese")),
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
    'pt-BR': _("Brazilian Portuguese"),
    'el': _("Greek"),
    'ru': _("Russian"),
    'ar': _("Arabic"),
    'ja': _("Japanese"),
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
    'PN' : 'PLNEBU',
    'LIN': 'GALAXY',
    'IG' : 'GALAXY',
    'GiG': 'GALAXY',
    'Sy2': 'GALAXY',
    'G'  : 'GALAXY',
}

SOLAR_SYSTEM_SUBJECT_CHOICES = (
    (0, _("Sun")),
    (1, _("Earth's Moon")),
    (2, _("Mercury")),
    (3, _("Venus")),
    (4, _("Mars")),
    (5, _("Jupiter")),
    (6, _("Saturn")),
    (7, _("Uranus")),
    (8, _("Neptune")),
    (9, _("Minor planet")),
    (10, _("Comet")),
    (11, _("Other")),
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


class GearMakeAutoRename(models.Model):
    rename_from = models.CharField(
        verbose_name = "Rename form",
        max_length = 128,
        primary_key = True,
        blank = False,
    )

    rename_to = models.CharField(
        verbose_name = "Rename to",
        max_length = 128,
        blank = False,
        null = False,
    )

    def __unicode__(self):
        return "%s --> %s" % (self.rename_from, self.rename_to)

    class Meta:
        app_label = 'astrobin'


class Gear(models.Model):
    make = models.CharField(
        verbose_name = _("Make"),
        help_text = _("The make, brand, producer or developer of this product."),
        max_length = 128,
        null = True,
        blank = True,
    )

    name = models.CharField(
        verbose_name = _("Name"),
        help_text = _("Just the name of this product, without any properties or personal customizations. Try to use the international name, in English language, if applicable. This name is shared among all users on AstroBin."),
        max_length = 128,
        null = False,
        blank = False,
    )

    master = models.ForeignKey('self', null = True, editable = False)

    commercial = models.ForeignKey(
        'CommercialGear',
        null = True,
        editable = False,
        on_delete = models.SET_NULL,
        related_name = 'base_gear',
    )

    retailed = models.ManyToManyField(
        'RetailedGear',
    )

    updated = models.DateTimeField(
        editable = False,
        auto_now = True,
        null = True,
        blank = True,
    )

    moderator_fixed =  models.DateTimeField(
        editable = False,
        null = True,
        blank = True,
    )

    def __unicode__(self):
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
        return '/gear/%i/%s/' % (self.id, self.slug())

    def slug(self):
        return slugify("%s %s" % (self.get_make(), self.get_name()))

    def hard_merge(self, slave):
        from astrobin.gear import get_correct_gear
        unused, master_gear_type = get_correct_gear(self.id)
        unused, slave_gear_type = get_correct_gear(slave.id)

        if master_gear_type != slave_gear_type:
            return

        # Find matching slaves in images
        images = Image.by_gear(slave)
        for image in images:
            for name, klass in Image.GEAR_CLASS_LOOKUP.iteritems():
                s = getattr(image, name).filter(pk = slave.pk)
                if s:
                    try:
                        getattr(image, name).add(klass.objects.get(pk = self.pk))
                        getattr(image, name).remove(s[0])
                    except klass.DoesNotExist:
                        continue

        # Find matching slaves in user profiles
        filters = reduce(operator.or_, [Q(**{'%s__gear_ptr__pk' % t: slave.pk}) for t in UserProfile.GEAR_CLASS_LOOKUP])
        owners = UserProfile.objects.filter(filters).distinct()
        for owner in owners:
            for name, klass in UserProfile.GEAR_CLASS_LOOKUP.iteritems():
                s = getattr(owner, name).filter(pk = slave.pk)
                if s:
                    try:
                        getattr(owner, name).add(klass.objects.get(pk = self.pk))
                        getattr(owner, name).remove(s[0])
                    except klass.DoesNotExist:
                        continue

        # Find matching slaves in deep sky acquisitions
        try:
            filter = Filter.objects.get(pk = self.pk)
            DeepSky_Acquisition.objects.filter(filter__pk = slave.pk).update(
                filter = filter)
        except Filter.DoesNotExist:
            pass

        # Find matching comments and move them to the master
        NestedComment.objects.filter(
            content_type = ContentType.objects.get(app_label = 'astrobin', model = 'gear'),
            object_id = slave.id
        ).update(object_id = self.id)

        # Find matching gear reviews and move them to the master
        reviews = Review.objects.filter(
            content_type = ContentType.objects.get(app_label = 'astrobin', model = 'gear'),
            content_id = slave.id
        ).update(content_id = self.id)

        # Fetch slave's master if this hard-merge's master doesn't have a soft-merge master
        if not self.master:
            self.master = slave.master
            self.save()

        # Steal the commercial gear and all the retailers
        if not self.commercial:
            self.commercial = slave.commercial
            self.save()

        for retailed in slave.retailed.all():
            if retailed not in self.retailed.all():
                self.retailed.add(retailed)

        GearHardMergeRedirect(fro = slave.pk, to = self.pk).save()
        slave.delete()


    def save(self, *args, **kwargs):
        try:
            autorename = GearMakeAutoRename.objects.get(rename_from = self.make)
            self.make = autorename.rename_to
        except:
            pass

        super(Gear, self).save(*args, **kwargs)

    def get_make(self):
        if self.commercial and self.commercial.proper_make:
            return self.commercial.proper_make
        if self.make:
            return self.make
        return ''

    def get_name(self):
        if self.commercial and self.commercial.proper_name:
            return self.commercial.proper_name
        return self.name

    class Meta:
        app_label = 'astrobin'
        ordering = ('-updated',)


class GearUserInfo(models.Model):
    gear = models.ForeignKey(
        Gear,
        editable = False,
    )

    user = models.ForeignKey(
        User,
        editable = False,
    )

    alias = models.CharField(
        verbose_name = _("Alias"),
        help_text = _("A descriptive name, alias or nickname for your own copy of this product."),
        max_length = 128,
        null = True,
        blank = True,
    )

    comment = models.TextField(
        verbose_name = _("Comment"),
        help_text = _("Information, description or comment about your own copy of this product."),
        null = True,
        blank = True,
    )

    def __unicode__(self):
        return "%s (%s)" % (self.alias, self.gear.name)

    class Meta:
        app_label = 'astrobin'
        unique_together = ('gear', 'user')


class GearAssistedMerge(models.Model):
    master = models.ForeignKey(Gear, related_name = 'assisted_master', null = True)
    slave  = models.ForeignKey(Gear, related_name = 'assisted_slave', null = True)
    cutoff = models.DecimalField(default = 0, max_digits = 3, decimal_places = 2)

    def __unicode__(self):
        return self.master.name

    class Meta:
        app_label = 'astrobin'


class GearHardMergeRedirect(models.Model):
    # Remembers what gears we merged, so we can perform URL redirects.
    fro = models.IntegerField()
    to = models.IntegerField()

    def __unicode__(self):
        return "%s -> %s" % (self.fro, self.to)

    class Meta:
        app_label = 'astrobin'


class Telescope(Gear):
    TELESCOPE_TYPES = (
        (0, _("Refractor: achromatic")),
        (1, _("Refractor: semi-apochromatic")),
        (2, _("Refractor: apochromatic")),
        (3, _("Refractor: non-achromatic Galilean")),
        (4, _("Refractor: non-achromatic Keplerian")),
        (5, _("Refractor: superachromat")),

        (6, _("Reflector: Dall-Kirkham")),
        (7, _("Reflector: Nasmyth")),
        (8, _("Reflector: Ritchey Chretien")),
        (9, _("Reflector: Gregorian")),
        (10, _("Reflector: Herschellian")),
        (11, _("Reflector: Newtonian")),

        (12, _("Catadioptric: Argunov-Cassegrain")),
        (13, _("Catadioptric: Klevtsov-Cassegrain")),
        (14, _("Catadioptric: Lurie-Houghton")),
        (15, _("Catadioptric: Maksutov")),
        (16, _("Catadioptric: Maksutov-Cassegrain")),
        (17, _("Catadioptric: modified Dall-Kirkham")),
        (18, _("Catadioptric: Schmidt camera")),
        (19, _("Catadioptric: Schmidt-Cassegrain")),
        (20, _("Catadioptric: ACF Schmidt-Cassegrain")),
        (21, _("Camera lens")),
        (22, _("Binoculars")),
    )

    aperture = models.DecimalField(
        verbose_name = _("Aperture"),
        help_text = _("(in mm)"),
        null = True,
        blank = True,
        max_digits = 8,
        decimal_places = 2,
    )

    focal_length = models.DecimalField(
        verbose_name = _("Focal length"),
        help_text = _("(in mm)"),
        null = True,
        blank = True,
        max_digits = 8,
        decimal_places = 2,
    )

    type = models.IntegerField(
        verbose_name = _("Type"),
        null = True,
        blank = True,
        choices = TELESCOPE_TYPES,
    )

    def attributes(self):
        return super(Telescope, self).attributes() +\
               [('aperture', _("mm")), ('focal_length', _("mm"))]

    class Meta:
        app_label = 'astrobin'


class Mount(Gear):
    max_payload = models.DecimalField(
        verbose_name = _("Max. payload"),
        help_text = _("(in kg)"),
        null = True,
        blank = True,
        max_digits = 6,
        decimal_places = 2,
    )

    pe = models.DecimalField(
        verbose_name = _("Periodic error"),
        help_text = _("(peak to peak, in arcseconds)"),
        null = True,
        blank = True,
        max_digits = 6,
        decimal_places = 2,
    )

    def attributes(self):
        return super(Mount, self).attributes() +\
               [('max_payload', _("kg")), ('pe', "\"")]

    class Meta:
        app_label = 'astrobin'


class Camera(Gear):
    CAMERA_TYPES = (
        (0, _("CCD")),
        (1, _("DSLR")),
        (2, _("Guider/Planetary")),
        (3, _("Film")),
        (4, _("Compact")),
        (5, _("Video camera")),
    )

    pixel_size = models.DecimalField(
        verbose_name = _("Pixel size"),
        help_text = _("(in &mu;m)"),
        null = True,
        blank = True,
        max_digits = 6,
        decimal_places = 2,
    )

    sensor_width = models.DecimalField(
        verbose_name = _("Sensor width"),
        help_text = _("(in mm)"),
        null = True,
        blank = True,
        max_digits = 6,
        decimal_places = 2,
    )

    sensor_height = models.DecimalField(
        verbose_name = _("Sensor height"),
        help_text = _("(in mm)"),
        null = True,
        blank = True,
        max_digits = 6,
        decimal_places = 2,
    )

    type = models.IntegerField(
        verbose_name = _("Type"),
        null = True,
        blank = True,
        choices = CAMERA_TYPES,
    )

    def attributes(self):
        return super(Camera, self).attributes() +\
               [('sensor_width', _("mm")), ('sensor_height', _("mm")), ('pixel_size', _("&mu;m"))]

    class Meta:
        app_label = 'astrobin'


class FocalReducer(Gear):
    class Meta:
        app_label = 'astrobin'


class Software(Gear):
    SOFTWARE_TYPES = (
        (0, _("Open source or freeware")),
        (1, _("Paid")),
    )

    type = models.IntegerField(
        verbose_name = _("Type"),
        null = True,
        blank = True,
        choices = SOFTWARE_TYPES,
    )

    class Meta:
        app_label = 'astrobin'


class Filter(Gear):
    FILTER_TYPES = (
        (0, _("Clear or color")),

        (1, _("Broadband: H-Alpha")),
        (2, _("Broadband: H-Beta")),
        (3, _("Broadband: S-II")),
        (4, _("Broadband: O-III")),
        (5, _("Broadband: N-II")),

        (6, _("Narrowband: H-Alpha")),
        (7, _("Narrowband: H-Beta")),
        (8, _("Narrowband: S-II")),
        (9, _("Narrowband: O-III")),
        (10, _("Narrowband: N-II")),

        (11, _("Light pollution suppression")),
        (12, _("Planetary")),
        (13, _("Other")),
        (14, _("UHC: Ultra High Contrast")),
    )

    type = models.IntegerField(
        verbose_name = _("Type"),
        null = True,
        blank = True,
        choices = FILTER_TYPES,
    )

    bandwidth = models.DecimalField(
        verbose_name = _("Bandwidth"),
        help_text = _("(in nm)"),
        null = True,
        blank = True,
        max_digits = 6,
        decimal_places = 2,
    )

    def attributes(self):
        return super(Filter, self).attributes() +\
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
        del(split[0])
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

    SUBJECT_TYPE_CHOICES = (
        (0, "---------"),
        (100, _("Deep sky object")),
        (200, _("Solar system body or event")),
        (300, _("Extremely wide field")),
        (400, _("Star trails")),
        (450, _("Northern lights")),
        (500, _("Gear")),
        (600, _("Other")),
    )

    DATA_SOURCE_TYPES = (
        'BACKYARD',
        'TRAVELLER',
        'OWN_REMOTE',
        'AMATEUR_HOSTING',
        'PUBLIC_AMATEUR_DATA',
        'PRO_DATA',
        'MIX',
        'OTHER',
        'UNKNOWN'
    )

    DATA_SOURCE_CHOICES = (
        (None, "---------"),
        (_("Self acquired"), (
            ("BACKYARD", _("Backyard")),
            ("TRAVELLER", _("Traveller")),
            ("OWN_REMOTE", _("Own remote observatory")),
        )),
        (_("Downloaded"), (
            ("AMATEUR_HOSTING", _("Amateur hosting facility")),
            ("PUBLIC_AMATEUR_DATA", _("Public amateur data")),
            ("PRO_DATA", _("Professional, scientific grade data")),
        )),
        (_("Other"), (
            ("MIX", _("Mix of multiple sources")),
            ("OTHER", _("None of the above")),
            ("UNKNOWN", _("Unknown")),
        )),
    )

    REMOTE_OBSERVATORY_CHOICES = (
        (None, "---------"),
        ("OWN", _("Non-commercial independent facility")),
        (None, "---------"),
        ("AC", "AstroCamp"),
        ("AHK", "Astro Hostel Krasnodar"),
        ("CS", "ChileScope"),
        ("DSP", "Dark Sky Portal"),
        ("DSC", "DeepSkyChile"),
        ("DSW", "DeepSkyWest"),
        ("eEyE", "e-EyE Extremadura"),
        ("GMO", "Grand Mesa Observatory"),
        ("HMO", "Heaven's Mirror Observatory"),
        ("IC", "IC Astronomy Observatories"),
        ("ITU", "Image The Universe"),
        ("iT", "iTelescope"),
        ("LGO", "Lijiang Gemini Observatory"),
        ("MARIO", "Marathon Remote Imaging Observatory (MaRIO)"),
        ("NMS", "New Mexico Skies"),
        ("OES", "Observatorio El Sauce"),
        ("RLD", "Riverland Dingo Observatory"),
        ("SS", "Sahara Sky"),
        ("SPVO", "San Pedro Valley Observatory"),
        ("SRO", "Sierra Remote Observatories"),
        ("SRO2", "Sky Ranch Observatory"),
        ("SPOO", "SkyPi Online Observatory"),
        ("SLO", "Slooh"),
        ("SSLLC", "Stellar Skies LLC"),

        ("OTHER", _("None of the above"))
    )

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

    title = models.CharField(
        max_length = 128,
        verbose_name = _("Title"),
    )

    subject_type = models.IntegerField(
        verbose_name = _("Subject type"),
        choices = SUBJECT_TYPE_CHOICES,
        default = 0,
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
        max_length=8,
        choices=REMOTE_OBSERVATORY_CHOICES,
        null=True,
        blank=True,
    )

    solar_system_main_subject = models.IntegerField(
        verbose_name = _("Main solar system subject"),
        help_text = _("If the main subject of your image is a body in the solar system, please select which (or which type) it is."),
        null = True,
        blank = True,
        choices = SOLAR_SYSTEM_SUBJECT_CHOICES,
    )

    locations = models.ManyToManyField(
        'astrobin.Location',
        verbose_name = _("Locations"),
        help_text = _("Drag items from the right side to the left side, or click on the plus sign."),
        blank = True,
    )

    description = models.TextField(
        null = True,
        blank = True,
        verbose_name = _("Description"),
        help_text = _("HTML tags are allowed."),
    )

    link = models.CharField(
        max_length = 256,
        null = True,
        blank = True,
     )

    link_to_fits = models.CharField(
        max_length = 256,
        null = True,
        blank = True,
     )

    image_file = models.ImageField(
        upload_to = image_upload_path,
        height_field = 'h',
        width_field = 'w',
        max_length = 256,
        null = True,
    )

    uploaded = models.DateTimeField(editable=False, auto_now_add=True)
    published = models.DateTimeField(editable=False, null=True, blank=True)
    updated = models.DateTimeField(editable=False, auto_now=True, null=True, blank=True)

    # For likes, bookmarks, and perhaps more.
    toggleproperties = GenericRelation(ToggleProperty)

    watermark_text = models.CharField(
        max_length = 128,
        null = True,
        blank = True,
        verbose_name = "Text",
    )

    watermark = models.BooleanField(
        default = False,
        verbose_name = _("Apply watermark to image"),
    )

    watermark_position = models.IntegerField(
        verbose_name = _("Position"),
        default = 0,
        choices = WATERMARK_POSITION_CHOICES,
    )

    watermark_size = models.CharField(
        max_length = 1,
        choices = WATERMARK_SIZE_CHOICES,
        default = 'M',
        verbose_name = _("Size"),
        help_text = _("The final font size will depend on how long your watermark is."),
    )

    watermark_opacity = models.IntegerField(
        default = 10,
    )

    # gear
    imaging_telescopes = models.ManyToManyField(Telescope, blank=True, related_name='imaging_telescopes', verbose_name=_("Imaging telescopes or lenses"))
    guiding_telescopes = models.ManyToManyField(Telescope, blank=True, related_name='guiding_telescopes', verbose_name=_("Guiding telescopes or lenses"))
    mounts = models.ManyToManyField(Mount, blank=True, verbose_name=_("Mounts"))
    imaging_cameras = models.ManyToManyField(Camera, blank=True, related_name='imaging_cameras', verbose_name=_("Imaging cameras"))
    guiding_cameras = models.ManyToManyField(Camera, blank=True, related_name='guiding_cameras', verbose_name=_("Guiding cameras"))
    focal_reducers = models.ManyToManyField(FocalReducer, blank=True, verbose_name=_("Focal reducers"))
    software = models.ManyToManyField(Software, blank=True, verbose_name=_("Software"))
    filters = models.ManyToManyField(Filter, blank=True, verbose_name=_("Filters"))
    accessories = models.ManyToManyField(Accessory, blank=True, verbose_name=_("Accessories"))

    user = models.ForeignKey(User)

    plot_is_overlay = models.BooleanField(editable=False, default=False)
    is_wip = models.BooleanField(editable=False, default=False)

    # Size of the image in bytes
    size = models.PositiveIntegerField(editable=False, default=0)

    w = models.IntegerField(editable=False, default=0)
    h = models.IntegerField(editable=False, default=0)
    animated = models.BooleanField(editable=False, default=False)

    license = models.IntegerField(
        choices = LICENSE_CHOICES,
        default = 0,
        verbose_name = _("License"),
    )

    is_final = models.BooleanField(
        editable = False,
        default = True
    )

    allow_comments = models.BooleanField(
        verbose_name = _("Allow comments"),
        default = True,
    )

    # 0 = undecided
    # 1 = approved
    # 2 = rejected
    moderator_decision = models.PositiveIntegerField(
        editable = False,
        default = 0,
    )

    moderated_when = models.DateTimeField(
        editable = False,
        null = True,
        auto_now_add = False,
        default = None,
    )

    moderated_by = models.ForeignKey(
        User,
        editable = False,
        null = True,
        related_name = 'images_moderated',
        on_delete = models.SET_NULL,
    )

    class Meta:
        app_label = 'astrobin'
        ordering = ('-uploaded', '-id')

    objects = PublicImagesManager()
    objects_including_wip = ImagesManager()
    wip = WipImagesManager()

    def __unicode__(self):
        return self.title if self.title is not None else _("(no title)")

    def get_absolute_url(self, revision = 'final', size = 'regular'):
        if revision == 'final':
            if not self.is_final:
                r = self.revisions.filter(is_final = True)
                if r:
                    revision = r[0].label

        url = '/'
        if size == 'full':
            url += 'full/'


        url += '%i/' % self.id

        if revision != 'final':
            url += '%s/' % revision

        return url

    def likes(self):
        key = "Image.%d.likes" % self.pk
        val = cache.get(key)
        if val is None:
            val = ToggleProperty.objects.toggleproperties_for_object("like", self).count()
            cache.set(key, val, 300)
        return val

    def liked_by(self):
        key = "Image.%d.liked_by" % self.pk
        val = cache.get(key)
        if val is None:
            user_pks = ToggleProperty.objects\
                .toggleproperties_for_object("like", self)\
                .select_related('user')\
                .values_list('user', flat = True)
            val = [profile.user for profile in UserProfile.objects.filter(user__pk__in = user_pks)]
            cache.set(key, val, 300)
        return val

    def bookmarks(self):
        key = "Image.%d.bookmarks" % self.pk
        val = cache.get(key)
        if val is None:
            val = ToggleProperty.objects.toggleproperties_for_object("bookmark", self).count()
            cache.set(key, val, 300)
        return val

    def bookmarked_by(self):
        key = "Image.%d.bookmarked_by" % self.pk
        val = cache.get(key)
        if val is None:
            user_pks = ToggleProperty.objects\
                .toggleproperties_for_object("bookmark", self)\
                .select_related('user')\
                .values_list('user', flat = True)
            val = [profile.user for profile in UserProfile.objects.filter(user__pk__in = user_pks)]
            cache.set(key, val, 300)
        return val

    def comments(self):
        from nested_comments.models import NestedComment
        key = "Image.%d.comments" % self.pk
        val = cache.get(key)
        if val is None:
            val = NestedComment.objects.filter(
                deleted = False,
                content_type__app_label = 'astrobin',
                content_type__model = 'image',
                object_id = self.id).count()
            cache.set(key, val, 300)
        return val

    def comments_by_distinct_users(self):
        from nested_comments.models import NestedComment
        key = "Image.%d.comments_by_distinct_users" % self.pk
        val = cache.get(key)
        if val is None:
            user_pks = NestedComment.objects.filter(
                deleted = False,
                content_type__app_label = 'astrobin',
                content_type__model = 'image',
                object_id = self.id)\
                    .select_related('author')\
                    .values_list('author', flat = True)\
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
                deleted = False,
                content_type__app_label = 'astrobin',
                content_type__model = 'image',
                object_id = self.id)\
                    .select_related('author')\
                    .values_list('author', flat = True)
            val = [profile.user for profile in UserProfile.objects.filter(user__pk__in = user_pks)]
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
                r = ImageRevision.objects.get(image = self, label = revision_label)
                field = r.image_file
            except ImageRevision.DoesNotExist:
                pass

        return field


    def get_final_revision_label(self):
        # Avoid hitting the db by potentially exitting early
        if self.is_final:
            return '0'

        for r in self.revisions.all():
            if r.is_final:
                return r.label

        return '0'


    def thumbnail_raw(self, alias, thumbnail_settings = {}):
        import urllib2
        from django.core.files.base import File, ContentFile
        from easy_thumbnails.files import get_thumbnailer
        from astrobin.s3utils import OverwritingFileSystemStorage

        revision_label = thumbnail_settings.get('revision_label', 'final')

        if revision_label is None:
            revision_label = 'final'

        # Compatibility
        if alias in ('revision', 'runnerup'):
            alias = 'thumb'

        log.debug("Image %d: requested raw thumbnail: %s / %s" % (self.id, alias, revision_label))

        options = settings.THUMBNAIL_ALIASES[''][alias].copy()

        field = self.get_thumbnail_field(revision_label);
        if not field.name.startswith('images/'):
            field.name = 'images/' + field.name

        local_path = None
        name = field.name

        if settings.AWS_S3_ENABLED:
            name_hash = field.storage.generate_local_name(name)

            log.debug("Image %s: starting with name = %s, local path = %s" % (self.id, name, local_path))

            # Try to generate the thumbnail starting from the file cache locally.
            if local_path is None:
                local_path = field.storage.local_storage.path(name_hash)

            try:
                log.debug("Image %s: trying local path %s" % (self.id, local_path))
                size = os.path.getsize(local_path)
                if size == 0:
                    log.debug("Image %s: size 0 in local path %s" % (self.id, local_path))
                    raise IOError("Empty file")

                with open(local_path):
                    thumbnailer = get_thumbnailer(
                        OverwritingFileSystemStorage(location = settings.IMAGE_CACHE_DIRECTORY),
                        name_hash)
                    log.debug("Image %d: got thumbnail from local file %s." % (self.id, name_hash))
            except (OSError, IOError, UnicodeEncodeError) as e:
                log.debug("Image %d: unable to get thumbnail from local file: %s" % (self.id, repr(e)))
                # If things go awry, fallback to getting the file from the remote
                # storage. But download it locally first if it doesn't exist, so
                # it can be used again later.
                log.debug("Image %d: getting remote file..." % self.id)

                # First try to get the file via URL, because that might hit the CloudFlare cache.
                url = settings.IMAGES_URL + name
                log.debug("Image %d: trying URL %s..." % (self.id, url))
                headers = { 'User-Agent': 'Mozilla/5.0' }
                req = urllib2.Request(url, None, headers)

                try:
                    remote_file = ContentFile(urllib2.urlopen(req).read())
                except (urllib2.HTTPError, urllib2.URLError):
                    remote_file = None

                # If that didn't work, we'll get the file rebularly via django-storages.
                if remote_file is None:
                    log.debug("Image %d: getting via URL didn't work. Falling back to django-storages..." % self.id)
                    try:
                        remote_file = field.storage._open(name)
                    except IOError:
                        # The remote file doesn't exist?
                        log.error("Image %d: the remote file doesn't exist?" % self.id)
                        return None

                try:
                    field.storage.local_storage._save(name_hash, remote_file)
                    thumbnailer = get_thumbnailer(
                        OverwritingFileSystemStorage(location = settings.IMAGE_CACHE_DIRECTORY),
                        name_hash)
                    log.debug("Image %d: saved local file %s." % (self.id, name_hash))
                except (OSError, UnicodeEncodeError):
                    log.error("Image %d: unable to save the local file." % self.id)
                    pass
        else:
            thumbnailer = get_thumbnailer(OverwritingFileSystemStorage(
                location = os.path.join(settings.UPLOADS_DIRECTORY)), name)

        if self.watermark and 'watermark' in options:
            options['watermark_text'] = self.watermark_text
            options['watermark_position'] = self.watermark_position
            options['watermark_size'] = self.watermark_size
            options['watermark_opacity'] = self.watermark_opacity

        try:
            thumb = thumbnailer.get_thumbnail(options)
            log.debug("Image %d: thumbnail generated." % self.id)
        except Exception as e:
            log.error("Image %d: unable to generate thumbnail: %s." % (self.id, e.message))
            return None

        return thumb


    def thumbnail_cache_key(self, field, alias):
        app_model = "{0}.{1}".format(
            self._meta.app_label,
            self._meta.object_name).lower()
        cache_key ='easy_thumb_alias_cache_%s.%s_%s' % (
            app_model,
            unicodedata.normalize('NFKD', unicode(field)).encode('ascii', 'ignore'),
            alias)

        from hashlib import sha256
        return sha256(cache_key).hexdigest()


    def thumbnail(self, alias, thumbnail_settings = {}):
        def normalize_url_security(url, thumbnail_settings):
            insecure = 'insecure' in thumbnail_settings and thumbnail_settings['insecure'] == True
            if insecure and url.startswith('https'):
                return url.replace('https', 'http', 1)
            if not insecure and url.startswith('http://'):
                return url.replace('http', 'https', 1)

            return url

        from astrobin_apps_images.models import ThumbnailGroup

        options = thumbnail_settings.copy()
        revision_label = options.get('revision_label', 'final')
        field = self.get_thumbnail_field(revision_label);
        if not field.name.startswith('images/'):
            field.name = 'images/' + field.name

        # For compatibility:
        if alias in ('revision', 'runnerup'):
            alias = 'thumb'

        if revision_label in (None, 'final'):
            revision_label = self.get_final_revision_label()
            options['revision_label'] = revision_label

        log.debug("Image %d: requested thumbnail: %s / %s" % (self.id, alias, revision_label))

        cache_key = self.thumbnail_cache_key(field, alias)

        # If this is an animated gif, let's just return the full size URL
        # because right now we can't thumbnail gifs preserving animation
        if 'animated' in options and options['animated'] == True:
            if alias in ('regular', 'hd', 'real'):
                url = settings.IMAGES_URL + field.name
                cache.set(cache_key + '_animated', url, 60*60*24*365)
                return normalize_url_security(url, thumbnail_settings)

        url = cache.get(cache_key)
        if url:
            log.debug("Image %d: got URL from cache entry %s" % (self.id, cache_key))
            return normalize_url_security(url, thumbnail_settings)

        # Not found in cache, attempt to fetch from database
        log.debug("Image %d: thumbnail not found in cache %s" % (self.id, cache_key))
        try:
            thumbnails = self.thumbnails.get(revision = revision_label)
            url = getattr(thumbnails, alias)
            if url:
                cache.set(cache_key, url, 60*60*24*365)
                log.debug("Image %d: thumbnail url found in database and saved into cache: %s" % (self.id, url))
                return normalize_url_security(url, thumbnail_settings)
        except ThumbnailGroup.DoesNotExist:
            log.debug("Image %d: there are no thumbnails in database." % self.id)
            try:
                ThumbnailGroup.objects.create(image = self, revision = revision_label)
            except IntegrityError:
                # Race condition
                pass

        # If we got down here, we don't have an url yet, so we start an asynchronous task and return a placeholder.
        from .tasks import retrieve_thumbnail
        task_id_cache_key = '%s.retrieve' % cache_key
        task_id = cache.get(task_id_cache_key)
        if task_id is None:
            result = retrieve_thumbnail.apply_async(args=(self.pk, alias, options), task_id=cache_key)
            cache.set(task_id_cache_key, result.task_id)
        else:
            AsyncResult(task_id_cache_key)

        return static('astrobin/images/placeholder-gallery.jpg')


    def thumbnail_invalidate_real(self, field, revision_label, delete_remote = True):
        from easy_thumbnails.files import get_thumbnailer

        from astrobin.s3utils import OverwritingFileSystemStorage
        from astrobin_apps_images.models import ThumbnailGroup

        log.debug("Image %d: invalidating thumbnails for field / label: %s / %s" % (self.id, field, revision_label))

        thumbnailer = get_thumbnailer(field)
        local_filename = field.storage.generate_local_name(field.name)
        local_thumbnailer = get_thumbnailer(
                OverwritingFileSystemStorage(location = settings.IMAGE_CACHE_DIRECTORY),
                local_filename)

        aliases = settings.THUMBNAIL_ALIASES['']
        for alias, thumbnail_settings in aliases.iteritems():
            options = settings.THUMBNAIL_ALIASES[''][alias].copy()
            if self.watermark and 'watermark' in options:
                options['watermark_text'] = self.watermark_text
                options['watermark_position'] = self.watermark_position
                options['watermark_size'] = self.watermark_size
                options['watermark_opacity'] = self.watermark_opacity

            # First we delete it from the cache
            cache_key = self.thumbnail_cache_key(field, alias)
            if cache.get(cache_key):
                log.debug("Image %d: deleting cache key %s" % (self.id, cache_key))
                cache.delete(cache_key)
            else:
                log.debug("Image %d: unable to find cache key %s" % (self.id, cache_key))

            # Then we delete the remote thumbnail
            if delete_remote:
                filename1 = thumbnailer.get_thumbnail_name(options)
                filename2 = thumbnailer.get_thumbnail_name(options, transparent = True)
                field.storage.delete(filename1)
                log.debug("Image %d: deleted remote file %s" % (self.id, filename1))
                field.storage.delete(filename2)
                log.debug("Image %d: deleted remote file %s" % (self.id, filename2))

                filename1 = local_thumbnailer.get_thumbnail_name(options)
                filename2 = local_thumbnailer.get_thumbnail_name(options, transparent = True)
                field.storage.delete(filename1)
                log.debug("Image %d: deleted remote file %s" % (self.id, filename1))
                field.storage.delete(filename2)
                log.debug("Image %d: deleted remote file %s" % (self.id, filename2))

                # Then delete local static storage image
                filenameLocal = os.path.join(field.storage.location, local_filename)
                field.storage.delete(filenameLocal)
                log.debug("Image %d: deleted remote file %s" % (self.id, filenameLocal))

            # Then we delete the local file cache
            if settings.AWS_S3_ENABLED:
                field.storage.local_storage.delete(local_filename)
                log.debug("Image %d: deleted local file %s" % (self.id, local_filename))

                try:
                    os.remove(os.path.join(field.storage.local_storage.location, local_filename))
                    log.debug("Image %d: removed local cache %s" % (self.id, local_filename))
                except OSError:
                    log.debug("Image %d: locally cached file not found." % self.id)

        # Then we remove the database entries
        try:
            thumbnailgroup = self.thumbnails.get(revision = revision_label).delete()
            log.debug("Image %d: removed thumbnail group." % self.id)
        except ThumbnailGroup.DoesNotExist:
            log.debug("Image %d: thumbnail group missing." % self.id)

    def thumbnail_invalidate(self, delete_remote = True):
        return self.thumbnail_invalidate_real(self.image_file, '0', delete_remote)

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

    def is_platesolvable(self):
        return self.subject_type in (100, 300)

    @staticmethod
    def by_gear(gear, gear_type = None):
        images = Image.objects.all()

        if gear_type:
            image_attr_lookup = {
                'Telescope': 'imaging_telescopes',
                'Camera': 'imaging_cameras',
                'Mount': 'mounts',
                'FocalReducer': 'focal_reducers',
                'Software': 'software',
                'Filter': 'filters',
                'Accessory': 'accessories',
            }

            images = images.filter(**{image_attr_lookup[gear_type]: gear})
        else:
            types = {
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

            filters = reduce(operator.or_, [Q(**{'%s__gear_ptr__pk' % t: gear.pk}) for t in types])
            images = images.filter(filters).distinct()

        return images


class ImageRevision(HasSolutionMixin, SafeDeleteModel):
    image = models.ForeignKey(
        Image,
        related_name = 'revisions'
    )

    image_file = models.ImageField(
        upload_to = image_upload_path,
        height_field = 'h',
        width_field = 'w',
        null = True,
        max_length = 256,
    )

    description = models.TextField(
        null = True,
        blank = True,
        verbose_name = _("Description"),
        help_text = _("HTML tags are allowed."),
    )

    uploaded = models.DateTimeField(editable=False, auto_now_add=True)

    # Size of the image in bytes
    size = models.PositiveIntegerField(editable=False, default=0)

    w = models.IntegerField(editable=False, default=0)
    h = models.IntegerField(editable=False, default=0)

    is_final = models.BooleanField(
        editable = False,
        default = False
    )

    label = models.CharField(
        max_length = 2,
        editable = False)

    class Meta:
        app_label = 'astrobin'
        ordering = ('uploaded', '-id')
        unique_together = ('image', 'label')

    def __unicode__(self):
        return self.image.title

    def get_absolute_url(self, revision = 'nd', size = 'regular'):
        # We can ignore the revision argument of course
        if size == 'full':
            return '/%i/%s/full/' % (self.image.id, self.label)

        return '/%i/%s/' % (self.image.id, self.label)

    def thumbnail_raw(self, alias, thumbnail_settings = {}):
        return self.image.thumbnail_raw(alias, dict(thumbnail_settings.items() + {'revision_label': self.label}.items()))

    def thumbnail(self, alias, thumbnail_settings = {}):
        return self.image.thumbnail(alias, dict(thumbnail_settings.items() + {'revision_label': self.label}.items()))

    def thumbnail_invalidate(self, delete_remote = True):
        return self.image.thumbnail_invalidate_real(self.image_file, self.label, delete_remote)


class Collection(models.Model):
    date_created = models.DateField(
        null = False,
        blank = False,
        auto_now_add = True,
        editable = False,
    )

    date_updated = models.DateField(
        null = False,
        blank = False,
        auto_now = True,
        editable = False,
    )

    user = models.ForeignKey(User)

    name = models.CharField(
        max_length = 256,
        null = False,
        blank = False,
        verbose_name = _("Name"),
    )

    description = models.TextField(
        null = True,
        blank = True,
        verbose_name = _("Description"),
    )

    images = models.ManyToManyField(
        Image,
        verbose_name = _("Images"),
        related_name = 'collections',
        blank = True,
    )

    cover = models.ForeignKey(
        Image,
        null = True,
        blank = True,
        verbose_name = _("Cover image"),
        on_delete = models.SET_NULL,
    )

    class Meta:
        app_label = 'astrobin'
        unique_together = ('user', 'name')
        ordering = ['name']

    def __unincode__(self):
        return "%s, a collectio by %s" % (self.name, self.user.username)


class Acquisition(models.Model):
    date = models.DateField(
        null = True,
        blank = True,
        verbose_name = _("Date"),
        help_text = _("Please use the following format: yyyy-mm-dd."),
    )

    image = models.ForeignKey(
        Image,
        verbose_name=_("Image"),
    )

    class Meta:
        app_label = 'astrobin'

    def __unicode__(self):
        return self.image.title

    def save(self, *args, **kwargs):
        super(Acquisition, self).save(*args, **kwargs)
        self.image.save()


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
        (5, _("5 - Suburban sky (ORANGE)")),
        (6, _("6 - Bright suburban sky (RED)")),
        (7, _("7 - Suburban/urban transition or Full Moon (RED)")),
        (8, _("8 - City sky (WHITE)")),
        (9, _("9 - Inner city sky (WHITE)")),
    )

    is_synthetic = models.BooleanField(
        _("Synthetic channel"),
        default = False)

    filter = models.ForeignKey(
        Filter,
        null=True, blank=True,
        verbose_name=_("Filter"),
        on_delete = models.SET_NULL)

    binning = models.IntegerField(
        null=True, blank=True,
        choices=BINNING_CHOICES,
        default=0,
        verbose_name=_("Binning"))

    number = models.IntegerField(
        _("Number"),
        null=True, blank=True,
        help_text=_("The number of sub-frames."))

    duration = models.IntegerField(
        _("Duration"),
        null=True, blank=True,
        help_text=_("Duration of each sub-frame, in seconds."))

    iso = models.IntegerField(
        _("ISO"),
        null=True, blank=True)

    gain = models.DecimalField(
        _("Gain"),
        null=True, blank=True,
        max_digits=5, decimal_places=2)

    sensor_cooling = models.IntegerField(
        _("Sensor cooling"),
        null=True, blank=True,
        help_text=_("The temperature of the chip. E.g.: -20."))

    darks = models.IntegerField(
        _("Darks"),
        null=True, blank=True,
        help_text=_("The number of dark frames."))

    flats = models.IntegerField(
        _("Flats"),
        null=True, blank=True,
        help_text=_("The number of flat frames."))

    flat_darks = models.IntegerField(
        _("Flat darks"),
        null=True, blank=True,
        help_text=_("The number of dark flat frames."))

    bias = models.IntegerField(
        _("Bias"),
        null=True, blank=True,
        help_text=_("The number of bias/offset frames."))

    bortle = models.IntegerField(
        verbose_name = _("Bortle Dark-Sky Scale"),
        null = True,
        blank = True,
        choices = BORTLE_CHOICES,
        help_text = _("Quality of the sky according to <a href=\"http://en.wikipedia.org/wiki/Bortle_Dark-Sky_Scale\" target=\"_blank\">the Bortle Scale</a>."),
    )

    mean_sqm = models.DecimalField(
        verbose_name = _("Mean mag/arcsec^2"),
        help_text = _("As measured with your Sky Quality Meter."),
        null=True, blank=True,
        max_digits=5, decimal_places=2)

    mean_fwhm = models.DecimalField(
        _("Mean FWHM"),
        null=True, blank=True,
        max_digits=5, decimal_places=2)

    temperature = models.DecimalField(
        _("Temperature"),
        null=True, blank=True,
        max_digits=5, decimal_places=2,
        help_text=_("Ambient temperature (in Centigrade degrees)."))


    advanced = models.BooleanField(
        editable=False,
        default=False)

    saved_on = models.DateTimeField(
        editable=False,
        auto_now=True,
        null=True)

    class Meta:
        app_label = 'astrobin'
        ordering = ['-saved_on', 'filter']


class SolarSystem_Acquisition(Acquisition):
    frames = models.IntegerField(
        null = True,
        blank = True,
        verbose_name = _("Number of frames"),
        help_text = _("The total number of frames you have stacked."),
    )

    fps = models.DecimalField(
        verbose_name = _("FPS"),
        help_text = _("Frames per second."),
        max_digits = 12,
        decimal_places = 5,
        null = True,
        blank = True,
    )

    focal_length = models.IntegerField(
        verbose_name = _("Focal length"),
        help_text = _("The focal length of the whole optical train, including barlow lenses or other components."),
        null = True,
        blank = True,
    )

    cmi = models.DecimalField(
        verbose_name = _("CMI"),
        help_text = _("Latitude of the first Central Meridian."),
        null = True,
        blank = True,
        max_digits = 5,
        decimal_places = 2,
    )

    cmii = models.DecimalField(
        verbose_name = _("CMII"),
        help_text = _("Latitude of the second Central Meridian."),
        null = True,
        blank = True,
        max_digits = 5,
        decimal_places = 2,
    )

    cmiii = models.DecimalField(
        verbose_name = _("CMIII"),
        help_text = _("Latitude of the third Central Meridian."),
        null = True,
        blank = True,
        max_digits = 5,
        decimal_places = 2,
    )

    seeing = models.IntegerField(
        verbose_name = _("Seeing"),
        help_text = _("Your estimation of the seeing, on a scale from 1 to 5."),
        null = True,
        blank = True,
    )

    transparency = models.IntegerField(
        verbose_name = _("Transparency"),
        help_text = _("Your estimation of the transparency, on a scale from 1 to 10."),
        null = True,
        blank = True
    )

    time = models.CharField(
        verbose_name = _("Time"),
        help_text = _("Please use the following format: hh:mm."),
        null = True,
        blank = True,
        max_length = 5,
    )

    class Meta:
        app_label = 'astrobin'


class Request(models.Model):
    from_user = models.ForeignKey(User, editable=False, related_name='requester')
    to_user   = models.ForeignKey(User, editable=False, related_name='requestee')
    fulfilled = models.BooleanField()
    message   = models.CharField(max_length=255)
    created   = models.DateTimeField(auto_now_add=True)

    objects   = InheritanceManager()

    def __unicode__(self):
        return '%s %s: %s' % (_('Request from'), self.from_user.username, self.message)

    class Meta:
        app_label = 'astrobin'
        ordering = ['-created']

    def get_absolute_url():
        return '/requests/detail/' + self.id + '/'


class ImageRequest(Request):
    TYPE_CHOICES = (
        ('INFO',     _('Additional information')),
        ('FITS',     _('TIFF/FITS')),
        ('HIRES',    _('Higher resolution')),
    )

    image = models.ForeignKey(Image, editable=False)
    type  = models.CharField(max_length=8, choices=TYPE_CHOICES)


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

    user = models.OneToOneField(User, editable=False)

    updated = models.DateTimeField(
        editable = False,
        auto_now = True,
        null = True,
        blank = True,
    )

    # Basic Information
    real_name = models.CharField(
        verbose_name = _("Real name"),
        help_text = _("If present, your real name will be used throughout the website."),
        max_length = 128,
        null = True,
        blank = True,
    )

    website = models.CharField(
        verbose_name = _("Website"),
        max_length = 128,
        null = True,
        blank = True,
    )

    job = models.CharField(
        verbose_name = _("Job"),
        max_length = 128,
        null = True,
        blank = True,
    )

    hobbies = models.CharField(
        verbose_name = _("Hobbies"),
        max_length = 128,
        null = True,
        blank = True,
        help_text = _("Do you have any hobbies other than astrophotography?"),
    )

    timezone = models.CharField(
        max_length=255,
        choices=PRETTY_TIMEZONE_CHOICES,
        blank=True, null=True,
        verbose_name=_("Timezone"),
        help_text=_("By selecting this, you will see all the dates on AstroBin in your timezone."))

    about = models.TextField(
        null = True,
        blank = True,
        verbose_name = _("About you"),
        help_text = _("Write something about yourself. HTML tags are allowed."),
    )

    # Counter for uploaded images.
    premium_counter = models.PositiveIntegerField(
        default = 0,
        editable = False
    )

    # Commercial information
    company_name = models.CharField(
        max_length = 128,
        null = True,
        blank = True,
        verbose_name = _("Company name"),
        help_text = _("The name of the company you represent on AstroBin."),
    )

    company_description = models.TextField(
        null = True,
        blank = True,
        verbose_name = _("Company description"),
        help_text = _("A short description of the company you represent on AstroBin. You can use some <a href=\"/faq/#comments\">formatting rules</a>."),
        validators = [MaxLengthValidator(1000)],
    )

    company_website = models.URLField(
        max_length = 512,
        null = True,
        blank = True,
        verbose_name = _("Company website"),
        help_text = _("The website of the company you represent on AstroBin."),
    )

    retailer_country = CountryField(
        verbose_name = _("Country of operation"),
        null = True,
        blank = True,
    )

    # Avatar
    avatar = models.CharField(max_length=64, editable=False, null=True, blank=True)

    exclude_from_competitions = models.BooleanField(
        default = False,
        verbose_name=_("I want to be excluded from competitions"),
        help_text=_("Check this box to be excluded from competitions and contests, such as the Image of the Day, the Top Picks, other custom contests. This will remove you from the leaderboards and hide your AstroBin Index."),
    )

    # Gear
    telescopes = models.ManyToManyField(Telescope, blank=True, verbose_name=_("Telescopes and lenses"), related_name='telescopes')
    mounts = models.ManyToManyField(Mount, blank=True, verbose_name=_("Mounts"), related_name='mounts')
    cameras = models.ManyToManyField(Camera, blank=True, verbose_name=_("Cameras"), related_name='cameras')
    focal_reducers = models.ManyToManyField(FocalReducer, blank=True, verbose_name=_("Focal reducers"), related_name='focal_reducers')
    software = models.ManyToManyField(Software, blank=True, verbose_name=_("Software"), related_name='software')
    filters = models.ManyToManyField(Filter, blank=True, verbose_name=_("Filters"), related_name='filters')
    accessories = models.ManyToManyField(Accessory, blank=True, verbose_name=_("Accessories"), related_name='accessories')

    default_frontpage_section = models.CharField(
        choices = (
            ('global', _("Global stream")),
            ('personal', _("Personal stream")),
            ('recent', _("All uploaded images")),
            ('followed', _("All images uploaded by people you follow")),
        ),
        default = 'global',
        max_length = 16,
        null = False,
        verbose_name = _("Default front page view"),
    )

    default_gallery_sorting = models.SmallIntegerField(
        choices = (
            (0, _("Upload time")),
            (1, _("Acquisition time")),
            (2, _("Subject type")),
            (3, _("Year")),
            (4, _("Gear")),
            (5, _("Collections")),
            (6, _("Title")),
        ),
        default = 0,
        null = False,
        verbose_name = _("Default gallery sorting"),
    )

    default_license = models.IntegerField(
        choices = LICENSE_CHOICES,
        default = 0,
        verbose_name = _("Default license"),
        help_text = _(
            "The license you select here is automatically applied to "
            "all your new images."
        ),
    )

    default_watermark_text = models.CharField(
        max_length = 128,
        null = True,
        blank = True,
        editable = False,
    )

    default_watermark = models.BooleanField(
        default = False,
        editable = False,
    )

    default_watermark_size = models.CharField(
        max_length = 1,
        default = 'M',
        choices = WATERMARK_SIZE_CHOICES,
        editable = False,
    )

    default_watermark_position = models.IntegerField(
        default = 0,
        choices = WATERMARK_POSITION_CHOICES,
        editable = False,
    )

    default_watermark_opacity = models.IntegerField(
        default = 10,
        editable = False,
    )

    accept_tos = models.BooleanField(
        editable=False,
        default=False
    )

    receive_important_communications = models.BooleanField(
        default=False,
        verbose_name=_(u'I accept to receive rare important communications via email'),
        help_text=_(u'This is highly recommended. These are very rare and contain information that you probably want to have.')
    )

    receive_newsletter = models.BooleanField(
        default=False,
        verbose_name=_(u'I accept to receive occasional newsletters via email'),
        help_text=_(u'Newsletters do not have a fixed schedule, but in any case they are not sent out more often than once per month.')
    )

    receive_marketing_and_commercial_material = models.BooleanField(
        default=False,
        verbose_name=_(u'I accept to receive occasional marketing and commercial material via email'),
        help_text=_(u'These emails may contain offers, commercial news, and promotions from AstroBin or its partners.')
    )

    # Preferences (notification preferences are stored in the django
    # notification model)
    language = models.CharField(
        max_length=8,
        null=True, blank=True,
        verbose_name=_("Language"),
        choices = LANGUAGE_CHOICES,
    )

    # One time notifications that won't disappear until marked as seen.

    seen_realname = models.BooleanField(
        default = False,
        editable = False,
    )

    seen_email_permissions = models.BooleanField(
        default=False,
        editable=False,
    )

    # PYBBM proxy fields
    @property
    def time_zone(self):
        import pytz
        from datetime import timedelta

        tz = self.timezone
        if tz is None:
            return 0

        now = datetime.now()
        try:
            offset = pytz.timezone(tz).utcoffset(now)
        except (pytz.NonExistentTimeError, pytz.AmbiguousTimeError):
            # If you're really unluckly, this offset results in a time that
            # doesn't actually exist because it's within the hour that gets
            # skipped when you enter DST.
            offset = pytz.timezone(tz).utcoffset(now + timedelta(hours=1))

        return offset.seconds / 3600

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

    def get_display_name(self):
        return self.real_name if self.real_name else self.user.__unicode__()

    def __unicode__(self):
        return self.get_display_name()

    def get_absolute_url(self):
        return '/users/%s' % self.user.username

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
        from haystack.exceptions import SearchFieldError
        from haystack.query import SearchQuerySet

        scores = {
            'user_scores_index': 0,
            'user_scores_followers': 0,
        }

        cache_key = "astrobin_user_score_%s" % self.user.username
        scores = cache.get(cache_key)

        if not scores:
            try:
                user_search_result =\
                    SearchQuerySet().models(User).filter(django_id = self.user.pk)[0]
            except (IndexError, SearchFieldError):
                return {
                    'user_scores_index': 0,
                    'user_scores_followers': 0
                }

            index = user_search_result.normalized_likes
            followers = user_search_result.followers

            scores = {}
            scores['user_scores_index'] = index
            scores['user_scores_followers'] = followers
            cache.set(cache_key, scores, 43200)

        return scores

    def is_moderator(self):
        return self.user.groups.filter(name = 'content_moderators')

    def is_image_moderator(self):
        return self.user.groups.filter(name = 'image_moderators')

    def is_iotd_staff(self):
        return self.user.groups.filter(name = 'iotd_staff')

    def is_iotd_submitter(self):
        return self.user.groups.filter(name = 'iotd_submitters')

    def is_iotd_reviewer(self):
        return self.user.groups.filter(name = 'iotd_reviewers')

    def is_iotd_judge(self):
        return self.user.groups.filter(name = 'iotd_judges')

    class Meta:
        app_label = 'astrobin'

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile, created = UserProfile.objects.get_or_create(user=instance)
post_save.connect(create_user_profile, sender=User)


class Location(models.Model):
    name = models.CharField(
        verbose_name = _("Name"),
        help_text = _("A descriptive name, e.g. 'Home observatory' or 'Mount Whitney'."),
        max_length = 255,
        null = True,
        blank = False,
    )
    city = models.CharField(
        verbose_name = _("City"),
        help_text = _("If this location is not in a city, use the name of the closest city."),
        max_length = 255,
        null = True,
        blank = False,
    )
    state = models.CharField(
        verbose_name = _("State or province"),
        max_length = 255,
        null = True, blank = True,
    )
    country = CountryField(
        verbose_name = _("Country"),
        null = True,
        blank = True,
    )
    lat_deg = models.IntegerField(
        null = True,
        blank = False,
    )
    lat_min = models.IntegerField(
        null = True, blank = True
    )
    lat_sec = models.IntegerField(
        null = True, blank = True
    )
    lat_side = models.CharField(
        default = 'N',
        max_length = 1,
        choices = (('N', _("North")), ('S', _("South"))),
        verbose_name = _('North or south'),
    )
    lon_deg = models.IntegerField(
        null = True,
        blank = False,
    )
    lon_min = models.IntegerField(
        null = True, blank = True
    )
    lon_sec = models.IntegerField(
        null = True, blank = True
    )
    lon_side = models.CharField(
        default = 'E',
        max_length = 1,
        choices = (('E', _("East")), ('W', _("West"))),
        verbose_name = _('East or West'),
    )

    altitude = models.IntegerField(
        verbose_name = _("Altitude"),
        help_text = _("In meters."),
        null = True, blank = True)

    user = models.ForeignKey(
        UserProfile,
        editable = False,
        null = True,
    )

    def __unicode__(self):
        return u', '.join(filter(None, [
            self.name, self.city, self.state,
            unicode(get_country_name(self.country))
        ]))

    class Meta:
        app_label = 'astrobin'


class App(models.Model):
    registrar = models.ForeignKey(
        User,
        editable = False,
        related_name = 'app_api_key')

    name = models.CharField(
        max_length = 256,
        blank = False)

    description = models.TextField(
        null = True,
        blank = True)

    key = models.CharField(
        max_length = 256,
        editable = False,
        blank = True,
        default = '')

    secret = models.CharField(
        max_length = 256,
        editable = False,
        blank = True,
        default = '')

    active = models.BooleanField(
        editable = False,
        default = True)

    created = models.DateTimeField(
        editable = False,
        auto_now_add = True)

    class Meta:
        ordering = ['-created']

    def __unicode__(self):
        return u"%s for %s" % (self.key, self.registrar)

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
        return hmac.new(str(new_uuid), digestmod=sha1).hexdigest()


class AppApiKeyRequest(models.Model):
    registrar = models.ForeignKey(
        User,
        editable = False,
        related_name = 'app_api_key_request')

    name = models.CharField(
        verbose_name = _("Name"),
        help_text = _("The name of the website or app that wishes to use the APIs."),
        max_length = 256,
        blank = False)

    description = models.TextField(
        null = True,
        blank = True,
        verbose_name = _("Description"),
        help_text = _("Please explain the purpose of your application, and how you intend to use the API."))

    approved = models.BooleanField(
        editable = False,
        default = False)

    created = models.DateTimeField(
        editable = False,
        auto_now_add = True)

    class Meta:
        ordering = ['-created']

    def __unicode__(self):
        return 'API request: %s' % self.name

    def save(self, *args, **kwargs):
        from django.core.mail.message import EmailMessage
        message = {
            'from_email': 'astrobin@astrobin.com',
            'to': ['astrobin@astrobin.com'],
            'subject': 'App API Key request from %s' % self.registrar.username,
            'body': 'Check the site\'s admin.',
        }
        EmailMessage(**message).send(fail_silently = False)

        return super(AppApiKeyRequest, self).save(*args, **kwargs)

    def approve(self):
        app, created = App.objects.get_or_create(
            registrar = self.registrar, name = self.name,
            description = self.description)

        self.approved = True
        self.save()

        if created:
            push_notification(
                [self.registrar], 'api_key_request_approved',
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
        related_name = 'image_of_the_day')

    date = models.DateField(
        auto_now_add = True)

    runnerup_1 = models.ForeignKey(
        Image,
        related_name = 'iotd_runnerup_1',
        null = True,
        on_delete = models.SET_NULL,
    )

    runnerup_2 = models.ForeignKey(
        Image,
        related_name = 'iotd_runnerup_2',
        null = True,
        on_delete = models.SET_NULL,
    )

    chosen_by = models.ForeignKey(
        User,
        related_name = "iotds_chosen",
        null = True,
        on_delete = models.SET_NULL,
    )

    class Meta:
        ordering = ['-date']
        app_label = 'astrobin'

    def __unicode__(self):
        return u"%s as an Image of the Day" % self.image.title


class ImageOfTheDayCandidate(models.Model):
    image = models.ForeignKey(
        Image,
        related_name = 'image_of_the_day_candidate')

    date = models.DateField(
        auto_now_add = True)

    position = models.PositiveIntegerField()

    def save(self, *args, **kwargs):
        if self.image.user.userprofile.exclude_from_competitions:
            raise ValidationError, "User is excluded from competitions"

        super(ImageOfTheDayCandidate, self).save(*args, **kwargs)

    class Meta:
        ordering = ['-date', 'position']
        app_label = 'astrobin'

    def __unicode__(self):
        return u"%s as an Image of the Day Candidate" % self.image.title


class GlobalStat(models.Model):
    date = models.DateField(
        editable = False,
        auto_now_add = True)

    users = models.IntegerField()
    images = models.IntegerField()
    integration = models.IntegerField()

    class Meta:
        ordering = ['-date']
        app_label = 'astrobin'

    def __unicode__(self):
        return u"%d users, %d images, %d hours of integration time" % (
            self.users, self.images, self.integration)


###############################################################################
# Commercial models.                                                          #
###############################################################################
class RetailedGear(models.Model):
    CURRENCY_CHOICES = (
        ('AUD', _('AUD - Australian dollars')),
        ('CAD', _('CAD - Canadian dollars')),
        ('CHF', _('CHF - Swiss francs')),
        ('EUR', _('EUR - Euros')),
        ('GBP', _('GPB - Pound stelings')),
        ('PLN', _('PLN - Polish zloty')),
        ('SEK', _('SEK - Swedish krona')),
        ('USD', _('USD - American dollars')),
    )

    retailer = models.ForeignKey(
        User,
        null = False,
        verbose_name = _("Producer"),
        related_name = 'retailed_gear',
        editable = False
    )


    link = models.URLField(
        max_length = 512,
        null = True,
        blank = True,
        verbose_name = _("Link"),
        help_text = _("The link to this product's page on your website."),
    )

    price = models.DecimalField(
        max_digits = 10,
        decimal_places = 2,
        null = True,
        blank = True,
        verbose_name = _("Price"),
    )

    currency = models.CharField(
        max_length = 3,
        choices = CURRENCY_CHOICES,
        default = 'EUR',
        blank = False,
        verbose_name = _("Currency"),
    )

    created = models.DateTimeField(
        auto_now_add = True,
        editable = False,
    )

    updated = models.DateTimeField(
        auto_now = True,
        editable = False,
    )

    class Meta:
        app_label = 'astrobin'
        ordering = ['created']
        verbose_name_plural = _("Retailed gear items")


class CommercialGear(models.Model):
    producer = models.ForeignKey(
        User,
        null = False,
        verbose_name = _("Producer"),
        related_name = 'commercial_gear',
        editable = False
    )

    proper_make = models.CharField(
        null = True,
        blank = True,
        max_length = 128,
        verbose_name = _("Proper make"),
        help_text = _("Sometimes, product make/brand/producer/developer names are not written properly by the users. Write here the proper make/brand/producer/developer name."),
    )

    proper_name = models.CharField(
        null = True,
        blank = True,
        max_length = 128,
        verbose_name = _("Proper name"),
        help_text = _("Sometimes, product names are not written properly by the users. Write here the proper product name, not including the make/brand/producer/developer name.<br/>It is recommended that you try to group as many items as possible, so try to use a generic version of your product's name."),
    )

    image = models.ForeignKey(
        Image,
        null = True,
        blank = True,
        verbose_name = _("Image"),
        help_text = _("The official, commercial image for this product. Upload an image via the regular uploading interface, set its subject type to \"Gear\", and then choose it from this list. If you upload several revisions, they will also appear in the commercial page."),
        related_name = 'featured_gear',
        on_delete = models.SET_NULL,
    )

    tagline = models.CharField(
        max_length = 256,
        null = True,
        blank = True,
        verbose_name = _("Tagline"),
        help_text = _("A memorable phrase that will sum up this product, for marketing purposes."),
    )

    link = models.URLField(
        max_length = 256,
        null = True,
        blank = True,
        verbose_name = _("Link"),
        help_text = _("The link to this product's page on your website."),
     )

    description = models.TextField(
        null = True,
        blank = True,
        verbose_name = _("Description"),
        help_text = _("Here you can write the full commercial description of your product. You can use some <a href=\"/faq/#comments\">formatting rules</a>."),
    )

    created = models.DateTimeField(
        auto_now_add = True,
        editable = False,
    )

    updated = models.DateTimeField(
        auto_now = True,
        editable = False,
    )

    def is_paid(self):
        return user_is_paying(self.producer)

    class Meta:
        app_label = 'astrobin'
        ordering = ['created']
        verbose_name_plural = _("Commercial gear items")


class BroadcastEmail(models.Model):
    subject = models.CharField(max_length=200)
    created = models.DateTimeField(default=timezone.now)
    message = tinymce_models.HTMLField()

    def __unicode__(self):
        return self.subject
