import uuid
from datetime import datetime
import os
import urllib2
import simplejson

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django import forms
from django.utils import translation
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.contrib.contenttypes import generic

from tasks import *

from djangoratings.fields import RatingField
from djangoratings.models import Vote

from model_utils.managers import InheritanceManager
from timezones.forms import PRETTY_TIMEZONE_CHOICES

from notifications import push_notification
from fields import *

from mptt.models import MPTTModel, TreeForeignKey

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
    ('en', _("English")),
    ('it', _("Italian")),
    ('es', _("Spanish")),
    ('fr', _("French")),
    ('fi', _("Finnish")),
    ('de', _("German")),
    ('nl', _("Dutch")),
    ('tr', _("Turkish")),
    ('sq', _("Albanian")),
)

LANGUAGES = {
    'en': _("English"),
    'it': _("Italian"),
    'es': _("Spanish"),
    'fr': _("French"),
    'fi': _("Finnish"),
    'de': _("German"),
    'nl': _("Dutch"),
    'tr': _("Turkish"),
    'sq': _("Albanian"),
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
    'Psr': SUBJECT_LABELS['PULSAR'],
    'GlC': SUBJECT_LABELS['GLOBUL'],
    'GCl': SUBJECT_LABELS['GLOBUL'],
    'OpC': SUBJECT_LABELS['OPENCL'],
    'HII': SUBJECT_LABELS['NEBULA'],
    'RNe': SUBJECT_LABELS['NEBULA'],
    'ISM': SUBJECT_LABELS['NEBULA'],
    'sh ': SUBJECT_LABELS['NEBULA'],
    'PN' : SUBJECT_LABELS['PLNEBU'],
    'LIN': SUBJECT_LABELS['GALAXY'],
    'IG' : SUBJECT_LABELS['GALAXY'],
    'GiG': SUBJECT_LABELS['GALAXY'],
    'Sy2': SUBJECT_LABELS['GALAXY'],
    'G'  : SUBJECT_LABELS['GALAXY'],
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
    make = models.CharField(
        verbose_name = _("Make"),
        max_length = 128,
        null = True,
        blank = True,
    )
    name = models.CharField(_("Name"), max_length=64)
    master = models.ForeignKey('self', null = True, editable = False)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'astrobin'


class GearAssistedMerge(models.Model):
    master = models.ForeignKey(Gear, related_name = 'assisted_master', null = True)
    slave  = models.ForeignKey(Gear, related_name = 'assisted_slave', null = True)
    cutoff = models.DecimalField(default = 0, max_digits = 3, decimal_places = 2)

    def __unicode__(self):
        return self.master.name

    class Meta:
        app_label = 'astrobin'


class GearAutoMerge(models.Model):
    master = models.ForeignKey(Gear)
    label = models.CharField(_("Label"), max_length = 64)

    def __unicode__(self):
        return self.label

    class Meta:
        app_label = 'astrobin'


class GearNeverMerge(models.Model):
    master = models.ForeignKey(Gear)
    label = models.CharField(_("Label"), max_length = 64)

    def __unicode__(self):
        return self.label

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
        (11, _("Reflector: Newtornian")),

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

    class Meta:
        app_label = 'astrobin'


class Camera(Gear):
    CAMERA_TYPES = (
        (0, _("CCD")),
        (1, _("DSLR")),
        (2, _("Guider/Planetary")),
        (3, _("Film")),
        (4, _("Compact")),
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
        help_text = _("(in &mu;m)"),
        null = True,
        blank = True,
        max_digits = 6,
        decimal_places = 2,
    )
  
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

class Subject(models.Model):
    # Simbad object id
    oid = models.IntegerField()
    # Right ascension
    ra = models.DecimalField(max_digits=8, decimal_places=5, null=True, blank=True)
    # Declination
    dec = models.DecimalField(max_digits=8, decimal_places=5, null=True, blank=True)
    # Main object identifier (aka main name)
    mainId = models.CharField(max_length=64, unique=True)
    # Object type
    otype = models.CharField(max_length=16, null=True, blank=True)
    # Morphological type
    mtype = models.CharField(max_length=16, null=True, blank=True)
    # Dimensions along the major and minor axis
    dim_majaxis = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    dim_minaxis = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Catalog name, i.e. fist word of a SIMBAD mainId
    catalog = models.CharField(max_length=64, null=True, blank=True)

    # id of the Subject, excluding the catalog name
    name = models.CharField(max_length=64, default = '')

    # The list of identifier (aka alternative names) is done via
    # a many-to-one relationship in SubjectIdentifier.

    def __unicode__(self):
        return self.mainId

    class Meta:
        app_label = 'astrobin'

    # Note: this function doesn't deal with the alternative names.
    def initFromJSON(self, json):
        for attr in [field.name for field in self._meta.fields]:
            if attr != 'id' and attr in json:
                setattr(self, attr, json[attr])

    def getFromSimbad(self):
        if not self.mainId:
            return
        url = settings.SIMBAD_SEARCH_URL + self.mainId
        f = None
        try:
            f = urllib2.urlopen(url)
        except:
            return;

        json = simplejson.loads(f.read())
        self.initFromJson(json)
        f.close()

    def save(self, *args, **kwargs):
        build_catalog_and_name(self, self.mainId)
        super(Subject, self).save(*args, **kwargs)


class SubjectIdentifier(models.Model):
    identifier = models.CharField(max_length=64, unique=True)
    subject = models.ForeignKey(Subject, related_name='idlist')

    # Catalog name, i.e. fist word of a SIMBAD mainId
    catalog = models.CharField(max_length=64, null=True, blank=True)

    # id of the Subject, excluding the catalog name
    name = models.CharField(max_length=64, default = '')

    class Meta:
        app_label = 'astrobin'

    def __unicode__(self):
        return self.identifier

    def save(self, *args, **kwargs):
        build_catalog_and_name(self, self.identifier)
        super(SubjectIdentifier, self).save(*args, **kwargs)


class Image(models.Model):
    BINNING_CHOICES = (
        (1, '1x1'),
        (2, '2x2'),
        (3, '3x3'),
        (4, '4x4'),
    )

    SOLVE_CHOICES = (
        (0, _("I don't want this image plate-solved.")),
        (1, _("This is not a deep sky image, don't plate-solve it.")),
        (2, _("I have no idea about the size of field, try a blind solve.")),
        (3, _("This is a very wide field image (more than 10 degrees).")),
        (4, _("This is a wide field image (1 to 10 degrees).")),
        (5, _("This ia narrow field image (less than 1 degree).")),
    )


    title = models.CharField(
        max_length = 128,
        verbose_name = _("Title"),
    )

    subjects = models.ManyToManyField(
        Subject,
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
    )

    description = models.TextField(
        null = True,
        blank = True,
        verbose_name = _("Description"),
        help_text = _("HTML tags are allowed."),
    )

    allow_rating = models.BooleanField(
        verbose_name = _("Allow rating"),
        default = True,
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

    filename = models.CharField(max_length=64, editable=False)
    original_ext = models.CharField(max_length=6, editable=False)
    uploaded = models.DateTimeField(editable=False, auto_now_add=True)
    updated = models.DateTimeField(editable=False, auto_now=True, null=True, blank=True)

    presolve_information = models.IntegerField(
        default = 0,
        choices = SOLVE_CHOICES,
        verbose_name = "",
    )

    focal_length = models.IntegerField(
        null = True,
        blank = True,
        help_text = _("(in mm)"),
        error_messages = {
            'required': _("Insert a focal length if you want to plate-solve."),
        },
        verbose_name = _("Focal length"),
    )

    pixel_size = models.DecimalField(
        null = True,
        blank = True,
        max_digits = 5,
        decimal_places = 2,
        help_text = _("(in &mu;m)"),
        error_messages = {
            'required': _("Insert a pixel size if you want to plate-solve."),
        },
        verbose_name = _("Pixel size"),
    )

    binning = models.IntegerField(
        null      = True,
        blank     = True,
        choices   = BINNING_CHOICES,
        default   = 1,
        help_text = _("This is the smallest of the binning values you used. If you imaged L in 1x1 and RGB in 2x2, put 1x1 here."),
        verbose_name = _("Binning"),
    )

    scaling = models.DecimalField(
        null = True,
        blank = True,
        max_digits = 6,
        decimal_places = 2,
        default = 100,
        help_text = _("If you scaled your image before uploading, enter here the percentage of the new size. E.g. 50 if you made it half the size. Cropping, instead, doesn't matter."),
        verbose_name = _("Scaling"),
    )

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

    watermark_opacity = models.IntegerField(
        default = 10,
    )

    # gear
    imaging_telescopes = models.ManyToManyField(Telescope, null=True, blank=True, related_name='imaging_telescopes', verbose_name=_("Imaging telescopes or lenses"))
    guiding_telescopes = models.ManyToManyField(Telescope, null=True, blank=True, related_name='guiding_telescopes', verbose_name=_("Guiding telescopes or lenses"))
    mounts = models.ManyToManyField(Mount, null=True, blank=True, verbose_name=_("Mounts"))
    imaging_cameras = models.ManyToManyField(Camera, null=True, blank=True, related_name='imaging_cameras', verbose_name=_("Imaging cameras")) 
    guiding_cameras = models.ManyToManyField(Camera, null=True, blank=True, related_name='guiding_cameras', verbose_name=_("Guiding cameras"))
    focal_reducers = models.ManyToManyField(FocalReducer, null=True, blank=True, verbose_name=_("Focal reducers")) 
    software = models.ManyToManyField(Software, null=True, blank=True, verbose_name=_("Software"))
    filters = models.ManyToManyField(Filter, null=True, blank=True, verbose_name=_("Filters"))
    accessories = models.ManyToManyField(Accessory, null=True, blank=True, verbose_name=_("Accessories"))

    rating = RatingField(range=5)
    votes = generic.GenericRelation(Vote)
    user = models.ForeignKey(User)

    is_stored = models.BooleanField(editable=False)
    is_solved = models.BooleanField(editable=False)
    plot_is_overlay = models.BooleanField(editable=False, default=False)
    is_wip = models.BooleanField(editable=False, default=False)
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

    was_revision = models.BooleanField(
        editable = False,
        default = False,
    )

    # astrometry
    ra_center_hms = models.CharField(
        null = True,
        blank = True,
        max_length = 12,
        editable = False,
    )
    dec_center_dms = models.CharField(
        null = True,
        blank = True,
        max_length = 13,
        editable = False,
    )
    pixscale = models.DecimalField(
        null = True,
        blank = True,
        max_digits = 14,
        decimal_places = 10,
        editable = False,
    )
    orientation = models.DecimalField(
        null = True,
        blank = True,
        max_digits = 14,
        decimal_places = 10,
        editable = False,
    )
    fieldw = models.DecimalField(
        null = True,
        blank = True,
        max_digits = 14,
        decimal_places = 10,
        editable = False,
    )
    fieldh = models.DecimalField(
        null = True,
        blank = True,
        max_digits = 14,
        decimal_places = 10,
        editable = False,
    )
    fieldunits = models.CharField(
        null = True,
        blank = True,
        max_length = 32,
        editable = False,
    )

    class Meta:
        app_label = 'astrobin'
        ordering = ('-uploaded', '-id')
        
    def __unicode__(self):
        return self.title if self.title is not None else _("(no title)")

    def save(self, *args, **kwargs):
        if self.id:
            try:
                image = Image.objects.get(id = self.id)
            except Image.DoesNotExist:
                # Abort!
                print "Aborting because image was deleted."
                return

        super(Image, self).save(*args, **kwargs)

        # Find requests and mark as fulfilled
        try:
            req = ImageRequest.objects.filter(
                image = self.id,
                type = 'INFO',
                fulfilled = False)
            for r in req:
                r.fulfilled = True
                r.save()
                push_notification(
                    [r.from_user], 'request_fulfilled',
                    {'object': self,
                     'object_url': settings.ASTROBIN_BASE_URL + self.get_absolute_url(),
                     'originator': r.to_user,
                     'originaror_url': r.to_user.get_absolute_url()})
        except:
            pass

    def process(self, solve=False):
        store_image.delay(self, solve=solve, lang=translation.get_language(), callback=image_stored_callback)

    def solve(self):
        solve_image.delay(self, lang=translation.get_language(), callback=image_solved_callback)

    def delete(self, *args, **kwargs):
        self.delete_data()

        # Delete references
        for r in ImageRequest.objects.filter(image=self):
            r.delete()

        # Delete revisions
        for r in ImageRevision.objects.filter(image=self):
            r.delete()

        super(Image, self).delete(*args, **kwargs)

    def delete_data(self):
        delete_image.delay(self.filename, self.original_ext)

    def get_absolute_url(self):
        return '/%i' % self.id


class ImageRevision(models.Model):
    image = models.ForeignKey(Image)
    filename = models.CharField(max_length=64, editable=False)
    original_ext = models.CharField(max_length=6, editable=False)
    uploaded = models.DateTimeField(editable=False, auto_now_add=True)

    w = models.IntegerField(editable=False, default=0)
    h = models.IntegerField(editable=False, default=0)

    is_stored = models.BooleanField(editable=False)
    is_solved = models.BooleanField(editable=False)

    is_final = models.BooleanField(
        editable = False,
        default = False
    )

    class Meta:
        app_label = 'astrobin'
        ordering = ('uploaded', '-id')
        
    def __unicode__(self):
        return 'Revision for %s' % self.image.title

    def save(self, *args, **kwargs):
        if self.id:
            try:
                r = ImageRevision.objects.get(id = self.id)
            except ImageRevision.DoesNotExist:
                # Abort!
                print "Aborting because image revision was deleted."
                return

        super(ImageRevision, self).save(*args, **kwargs)

    def process(self):
        store_image.delay(self, solve=False, lang=translation.get_language(), callback=image_stored_callback)

    def delete(self, *args, **kwargs):
        delete_data = not kwargs.pop('dont_delete_data', False)
        if delete_data: 
            delete_image.delay(self.filename, self.original_ext) 
        super(ImageRevision, self).delete(*args, **kwargs)

    def get_absolute_url(self):
        return '/%i?r=%i' % (self.image.id, self.id)
 

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
        _("Synthetic channel"))

    filter = models.ForeignKey(
        Filter,
        null=True, blank=True,
        verbose_name=_("Filter"))

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


class ABPOD(models.Model):
    image = models.ForeignKey(Image, unique=True, verbose_name=_("Image"))
    date = models.DateTimeField(_("Date"))

    def __unicode__(self):
        return self.image.title

    class Meta:
        app_label = 'astrobin'


class MessierMarathonNominations(models.Model):
    messier_number = models.IntegerField()
    image = models.ForeignKey(Image)
    nominations = models.IntegerField(default = 0)
    nominators = models.ManyToManyField(User, null=True)

    def __unicode__(self):
        return 'M %i' % self.messier_number

    class Meta:
        app_label = 'astrobin'
        unique_together = ('messier_number', 'image')
        ordering = ('messier_number', 'nominations')


class MessierMarathon(models.Model):
    messier_number = models.IntegerField(primary_key = True)
    image = models.ForeignKey(Image)

    def __unicode__(self):
        return 'M %i' % self.messier_number

    class Meta:
        app_label = 'astrobin'
        ordering = ('messier_number',)


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


class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True, editable=False)

    # Basic Information
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

    # Avatar
    avatar = models.CharField(max_length=64, editable=False, null=True, blank=True)

    # Gear
    telescopes = models.ManyToManyField(Telescope, null=True, blank=True, verbose_name=_("Telescopes and lenses"))
    mounts = models.ManyToManyField(Mount, null=True, blank=True, verbose_name=_("Mounts"))
    cameras = models.ManyToManyField(Camera, null=True, blank=True, verbose_name=_("Cameras"))
    focal_reducers = models.ManyToManyField(FocalReducer, null=True, blank=True, verbose_name=_("Focal reducers"))
    software = models.ManyToManyField(Software, null=True, blank=True, verbose_name=_("Software"))
    filters = models.ManyToManyField(Filter, null=True, blank=True, verbose_name=_("Filters"))
    accessories = models.ManyToManyField(Accessory, null=True, blank=True, verbose_name=_("Accessories"))

    follows = models.ManyToManyField('self', null=True, blank=True, related_name='followers', symmetrical=False)

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

    default_watermark_position = models.IntegerField(
        default = 0,
        choices = WATERMARK_POSITION_CHOICES,
        editable = False,
    )

    default_watermark_opacity = models.IntegerField(
        default = 10,
        editable = False,
    )

    # Preferences (notification preferences are stored in the django
    # notification model)
    language = models.CharField(
        max_length=8,
        null=True, blank=True,
        verbose_name=_("Language"),
        choices = LANGUAGE_CHOICES,
    )

    def __unicode__(self):
        return "%s' profile" % self.user.username

    def get_absolute_url(self):
        return '/users/%s' % self.user.username

    class Meta:
        app_label = 'astrobin'


class Comment(MPTTModel):
    image = models.ForeignKey(
        Image,
    )
    author = models.ForeignKey(
        User,
    )
    comment = models.TextField(
        verbose_name = "",
    )
    is_deleted = models.BooleanField(
        default = False,
    )
    added  = models.DateTimeField(
        auto_now_add = True,
        editable = False,
    )
    parent = TreeForeignKey(
        'self',
        null = True,
        blank = True,
        editable = False,
        related_name = 'children'
    )

    def save(self, *args, **kwargs):
        if not self.id:
            Comment.tree.insert_node(self, self.parent)
        super(Comment, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.comment

    class MPTTMeta:
        order_insertion_by = ['added']

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
        if self.state:
            return '%s, %s (%s), %s' % (self.name, self.city, self.state, get_country_name(self.country))
        else:
            return '%s, %s, %s' % (self.name, self.city, get_country_name(self.country))

    class Meta:
        app_label = 'astrobin'


class Favorite(models.Model):
    image = models.ForeignKey(Image)
    user = models.ForeignKey(User)
    created = models.DateTimeField(auto_now_add = True)

    class Meta:
        app_label = 'astrobin'
        ordering = ('-created',)


from zinnia.models import Entry
def blog_entry_notify(sender, instance, created, **kwargs):
    if created:
         push_notification(
            User.objects.all(),
            'new_blog_entry',
            {
                'object': instance.title,
                'object_url': instance.get_absolute_url()
            }
         )

post_save.connect(blog_entry_notify, sender = Entry)

