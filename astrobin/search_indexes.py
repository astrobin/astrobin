# Python
import string
import re
import datetime

# Django
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

# Third party apps
from haystack.indexes import *
from haystack import site
from hitcount.models import HitCount
from toggleproperties.models import ToggleProperty

# This app
from astrobin.models import Image
from astrobin.models import DeepSky_Acquisition
from astrobin.models import SolarSystem_Acquisition
from astrobin.models import UserProfile
from astrobin.models import Gear, CommercialGear, RetailedGear

from astrobin.utils import unique_items

# Other AstroBin apps
from nested_comments.models import NestedComment


def _get_integration(image):
    deep_sky_acquisitions = DeepSky_Acquisition.objects.filter(image=image)
    solar_system_acquisition = None
    integration = 0

    try:
        solar_system_acquisition = SolarSystem_Acquisition.objects.get(image=image)
    except:
        pass

    if deep_sky_acquisitions:
        for a in deep_sky_acquisitions:
            if a.duration and a.number:
                integration += (a.duration * a.number)
    elif solar_system_acquisition:
        return 0

    return integration


def _prepare_likes(obj):
    return ToggleProperty.objects.toggleproperties_for_object("like", obj).count()

def _prepare_moon_phase(obj):
    from moon import MoonPhase

    deep_sky_acquisitions = DeepSky_Acquisition.objects.filter(image=obj)
    moon_illuminated_list = []
    if deep_sky_acquisitions:
        for a in deep_sky_acquisitions:
            if a.date is not None:
                m = MoonPhase(a.date)
                moon_illuminated_list.append(m.illuminated * 100.0)

    if len(moon_illuminated_list) == 0:
        # We must make an assumption between 0 and 100, or this won't
        # show up in any searches.
        return 0

    return sum(moon_illuminated_list) / float(len(moon_illuminated_list))

def _prepare_first_acquisition_date(obj):
    deep_sky_acquisitions = DeepSky_Acquisition.objects.filter(image=obj)
    solar_system_acquisition = None

    try:
        solar_system_acquisition = SolarSystem_Acquisition.objects.get(image=obj)
    except:
        pass

    date = None
    if deep_sky_acquisitions:
        date = deep_sky_acquisitions[0].date
        for a in deep_sky_acquisitions:
            if a.date is not None and date is not None:
                if a.date < date:
                    date = a.date
    elif solar_system_acquisition:
        date = solar_system_acquisition.date

    return date

def _prepare_last_acquisition_date(obj):
    deep_sky_acquisitions = DeepSky_Acquisition.objects.filter(image=obj)
    solar_system_acquisition = None

    try:
        solar_system_acquisition = SolarSystem_Acquisition.objects.get(image=obj)
    except:
        pass

    date = None
    if deep_sky_acquisitions:
        date = deep_sky_acquisitions[0].date
        for a in deep_sky_acquisitions:
            if a.date is not None and date is not None:
                if a.date > date:
                    date = a.date
    elif solar_system_acquisition:
        date = solar_system_acquisition.date

    return date if date else datetime.datetime.min

def _prepare_views(obj, content_type):
    views = 0
    try:
        views = HitCount.objects.get(object_pk = obj.pk, content_type__name = content_type).hits
    except: 
        pass

    return views

def _prepare_min_aperture(obj):
    d = 0
    for telescope in obj.imaging_telescopes.all():
        if telescope.aperture is not None and (d == 0 or telescope.aperture < d):
            d = int(telescope.aperture)
    return d

def _prepare_max_aperture(obj):
    import sys
    d = sys.maxint
    for telescope in obj.imaging_telescopes.all():
        if telescope.aperture is not None and (d == sys.maxint or telescope.aperture > d):
            d = int(telescope.aperture)
    return d

def _prepare_min_pixel_size(obj):
    s = 0
    for camera in obj.imaging_cameras.all():
        if camera.pixel_size is not None and (s == 0 or camera.pixel_size < s):
            s = int(camera.pixel_size)
    return s

def _prepare_max_pixel_size(obj):
    import sys
    s = sys.maxint
    for camera in obj.imaging_cameras.all():
        if camera.pixel_size is not None and (s == sys.maxint or camera.pixel_size > s):
            s = int(camera.pixel_size)
    return s

def _prepare_telescope_types(obj):
    return [x.type for x in obj.imaging_telescopes.all()]

def _prepare_camera_types(obj):
    return [x.type for x in obj.imaging_cameras.all()]

def _prepare_comments(obj):
    ct = ContentType.objects.get(app_label = 'astrobin', model = 'image')
    return NestedComment.objects.filter(
        content_type = ct,
        object_id = obj.id,
        deleted = False).count()


class GearIndex(SearchIndex):
    model_weight = IntegerField()

    text = CharField(document=True, use_template=True)

    images = IntegerField()

    # Total likes of all images taken with this item.
    likes = IntegerField()

    # Total integration of images taken with this item.
    integration = FloatField()

    # Total views on images taken with this item.
    views = IntegerField()

    # Number of bookmarks on images taken with this item.
    bookmarks = IntegerField()

    # Number of comments on images taken with this item.
    comments = IntegerField()

    producers = MultiValueField()
    retailers = MultiValueField()

    def index_queryset(self):
        return Gear.objects\
            .exclude(commercial = None)\
            .filter(commercial__producer__groups__name = 'Paying')

    def get_model(self):
        return Gear

    def get_images(self, obj):
        filters = (\
            Q(imaging_telescopes = obj) |\
            Q(guiding_telescopes = obj) |\
            Q(mounts = obj) |\
            Q(imaging_cameras = obj) |\
            Q(guiding_cameras = obj) |\
            Q(focal_reducers = obj) |\
            Q(software = obj) |\
            Q(filters = obj) |\
            Q(accessories = obj)\
        )
        return Image.objects.filter(filters).distinct()

    def prepare_model_weight(self, obj):
        # Printing here just because it's the first "prepare" function.
        print "%s: %d" % (obj.__class__.__name__, obj.pk)
        return 100;

    def prepare_images(self, obj):
        return len(self.get_images(obj))

    def prepare_likes(self, obj):
        likes = 0
        for i in self.get_images(obj):
            likes += ToggleProperty.objects.toggleproperties_for_object("like", i).count()

        return likes

    def prepare_integration(self, obj):
        integration = 0
        for i in self.get_images(obj):
            integration += _get_integration(i)

        return integration / 3600.0

    def prepare_views(self, obj):
        views = 0
        for i in self.get_images(obj):
            views += _prepare_views(i, 'image')
        return views

    def prepare_bookmarks(self, obj):
        bookmarks = 0
        for i in self.get_images(obj):
            bookmarks += ToggleProperty.objects.toggleproperties_for_object("bookmark", i).count()
        return bookmarks

    def prepare_comments(self, obj):
        comments = 0
        for i in self.get_images(obj):
            comments += _prepare_comments(i)
        return comments

    def prepare_producers(self, obj):
        producers = CommercialGear.objects\
            .filter(base_gear = obj)\
            .exclude(Q(producer__userprofile__company_name = None) | Q(producer__userprofile__company_name = ""))
        return ["%s" % x.producer.userprofile.company_name for x in producers]

    def prepare_retailers(self, obj):
        retailers = RetailedGear.objects\
            .filter(gear = obj)\
            .exclude(Q(retailer__userprofile__company_name = None) | Q(retailer__userprofile__company_name = ""))
        return ["%s" % x.retailer.userprofile.company_name for x in retailers]


class UserIndex(SearchIndex):
    model_weight = IntegerField()

    text = CharField(document=True, use_template=True)
    images = IntegerField()
    avg_integration = FloatField()

    # Total likes of all user's images.
    likes = IntegerField()

    # Total likes of all user's images.
    average_likes = FloatField()

    # Normalized likes (best images only)
    normalized_likes = FloatField()

    # Number of followers
    followers = IntegerField()

    # Total user ingegration.
    integration = FloatField()

    # Average moon phase under which this user has operated.
    moon_phase = FloatField()

    # First and last acquisition dates, including all images of course.
    first_acquisition_date = DateTimeField()
    last_acquisition_date = DateTimeField()

    # Total views from all images.
    views = IntegerField()

    # Min and max aperture of all telescopes used in this user's images.
    min_aperture = IntegerField()
    max_aperture = IntegerField()

    # Min and max pixel size of all cameras used in this user's images.
    min_pixel_size = IntegerField()
    max_pixel_size = IntegerField()

    # Number of bookmarks on own images
    bookmarks = IntegerField()

    # Types of telescopes and cameras with which this user has imaged.
    telescope_types = MultiValueField()
    camera_types = MultiValueField()

    comments = IntegerField()
    comments_written = IntegerField()

    username = CharField(model_attr = 'username')

    def index_queryset(self):
        return User.objects.all()

    def get_model(self):
        return User

    def prepare_model_weight(self, obj):
        # Printing here just because it's the first "prepare" function.
        print "%s: %d" % (obj.__class__.__name__, obj.pk)
        return 200;

    def prepare_images(self, obj):
        return Image.objects.filter(user = obj).count()

    def prepare_avg_integration(self, obj):
        integration = 0
        images = 0
        for i in Image.objects.filter(user = obj):
            image_integration = _get_integration(i)
            if image_integration:
                images += 1
                integration += image_integration

        return (integration / 3600.0) / images if images else 0


    def prepare_likes(self, obj):
        likes = 0
        for i in Image.objects.filter(user = obj):
            likes += ToggleProperty.objects.toggleproperties_for_object("like", i).count()
        return likes

    def prepare_average_likes(self, obj):
        likes = self.prepare_likes(obj)
        images = self.prepare_images(obj)

        return likes / float(images) if images > 0 else 0

    def prepare_normalized_likes(self, obj):
        def average(values):
            if len(values):
                return sum(values) / float(len(values))
            return 0

        def index(values):
            import math
            return average(values) * math.log(len(values)+1, 10)

        avg = self.prepare_average_likes(obj)
        norm = []

        for i in Image.objects.filter(user = obj):
            likes = i.likes()
            if likes >= avg:
                norm.append(likes)

        if len(norm) == 0:
            return 0

        return index(norm)


    def prepare_followers(self, obj):
        return ToggleProperty.objects.filter(
            property_type = "follow",
            content_type = ContentType.objects.get_for_model(User),
            object_id = obj.pk
        ).count()

    def prepare_integration(self, obj):
        integration = 0
        for i in Image.objects.filter(user = obj):
            integration += _get_integration(i)

        return integration / 3600.0

    def prepare_moon_phase(self, obj):
        l = []
        for i in Image.objects.filter(user = obj):
            l.append(_prepare_moon_phase(i))
        if len(l) == 0:
            return 0
        return reduce(lambda x, y: x + y, l) / len(l)

    def prepare_first_acquisition_date(self, obj):
        l = []
        for i in Image.objects.filter(user = obj):
            l.append(_prepare_first_acquisition_date(obj))
        if len(l) == 0:
            return None
        return min(l)

    def prepare_last_acquisition_date(self, obj):
        l = []
        for i in Image.objects.filter(user = obj):
            l.append(_prepare_last_acquisition_date(obj))
        if len(l) == 0:
            return None
        return max(l)

    def prepare_views(self, obj):
        views = 0
        for i in Image.objects.filter(user = obj):
            views += _prepare_views(i, 'image')
        return views

    def prepare_min_aperture(self, obj):
        l = []
        for i in Image.objects.filter(user = obj):
            l.append(_prepare_min_aperture(i))
        if len(l) == 0:
            return 0
        return min(l)

    def prepare_max_aperture(self, obj):
        l = []
        for i in Image.objects.filter(user = obj):
            l.append(_prepare_max_aperture(i))
        if len(l) == 0:
            return 0
        return max(l)

    def prepare_min_pixel_size(self, obj):
        l = []
        for i in Image.objects.filter(user = obj):
            l.append(_prepare_min_pixel_size(i))
        if len(l) == 0:
            return 0
        return min(l)

    def prepare_max_pixel_size(self, obj):
        l = []
        for i in Image.objects.filter(user = obj):
            l.append(_prepare_max_pixel_size(i))
        if len(l) == 0:
            return 0
        return max(l)

    def prepare_bookmarks(self, obj):
        bookmarks = 0
        for i in Image.objects.filter(user = obj):
            bookmarks += ToggleProperty.objects.toggleproperties_for_object("bookmark", i).count()
        return bookmarks

    def prepare_telescope_types(self, obj):
        l = []
        for i in Image.objects.filter(user = obj):
            l += _prepare_telescope_types(i)
        return unique_items(l)

    def prepare_camera_types(self, obj):
        l = []
        for i in Image.objects.filter(user = obj):
            l += _prepare_camera_types(i)
        return unique_items(l)

    def prepare_comments(self, obj):
        comments = 0
        for i in Image.objects.filter(user = obj):
            comments += _prepare_comments(i)
        return comments

    def prepare_comments_written(self, obj):
        return NestedComment.objects.filter(author = obj, deleted = False).count()


class ImageIndex(SearchIndex):
    model_weight = IntegerField()

    text = CharField(document=True, use_template=True)

    uploaded = DateTimeField(model_attr='uploaded')

    likes = IntegerField()
    integration = FloatField()
    moon_phase = FloatField()
    first_acquisition_date = DateTimeField()
    last_acquisition_date = DateTimeField()
    views = IntegerField()

    solar_system_main_subject = IntegerField()

    is_deep_sky = BooleanField()
    is_clusters = BooleanField()
    is_nebulae = BooleanField()
    is_galaxies = BooleanField()

    is_solar_system = BooleanField()
    is_sun = BooleanField()
    is_moon = BooleanField()
    is_planets = BooleanField()
    is_comets = BooleanField()

    license = IntegerField(model_attr = 'license')

    min_aperture = IntegerField()
    max_aperture = IntegerField()

    min_pixel_size = IntegerField()
    max_pixel_size = IntegerField()

    bookmarks = IntegerField()

    telescope_types = MultiValueField()
    camera_types = MultiValueField()

    comments = IntegerField()

    is_commercial = BooleanField()

    subject_type = IntegerField(model_attr = 'subject_type')

    username = CharField(model_attr = 'user__username')

    def index_queryset(self):
        return Image.objects.filter(moderator_decision = 1)

    def get_model(self):
        return Image

    def prepare_model_weight(self, obj):
        # Printing here just because it's the first "prepare" function.
        print "%s: %d" % (obj.__class__.__name__, obj.pk)
        return 300;

    def prepare_likes(self, obj):
        return _prepare_likes(obj)

    def prepare_integration(self, obj):
        return _get_integration(obj)

    def prepare_moon_phase(self, obj):
        return _prepare_moon_phase(obj)

    def prepare_first_acquisition_date(self, obj):
        return _prepare_first_acquisition_date(obj)

    def prepare_last_acquisition_date(self, obj):
        return _prepare_last_acquisition_date(obj)

    def prepare_views(self, obj):
        return _prepare_views(obj, 'image')

    def prepare_solar_system_main_subject(self, obj):
        return obj.solar_system_main_subject


    def prepare_is_deep_sky(self, obj):
        return DeepSky_Acquisition.objects.filter(image = obj).count() > 0

    def prepare_is_solar_system(self, obj):
        if obj.solar_system_main_subject:
            return True

        if SolarSystem_Acquisition.objects.filter(image = obj):
            return True

        return False

    def prepare_is_sun(self, obj):
        return obj.solar_system_main_subject == 0

    def prepare_is_moon(self, obj):
        return obj.solar_system_main_subject == 1

    def prepare_is_planets(self, obj):
        return obj.solar_system_main_subject in range(2, 8)

    def prepare_is_comets(self, obj):
        return obj.solar_system_main_subject == 10

    def prepare_min_aperture(self, obj):
        return _prepare_min_aperture(obj)

    def prepare_max_aperture(self, obj):
        return _prepare_max_aperture(obj)

    def prepare_min_pixel_size(self, obj):
        return _prepare_min_pixel_size(obj)
        s = 0
        for camera in obj.imaging_cameras.all():
            if camera.pixel_size is not None and (s == 0 or camera.pixel_size < s):
                s = int(camera.pixel_size)
        return s

    def prepare_max_pixel_size(self, obj):
        return _prepare_max_pixel_size(obj)
        import sys
        s = sys.maxint
        for camera in obj.imaging_cameras.all():
            if camera.pixel_size is not None and (s == sys.maxint or camera.pixel_size > s):
                s = int(camera.pixel_size)
        return s

    def prepare_bookmarks(self, obj):
        return ToggleProperty.objects.toggleproperties_for_object("bookmark", obj).count()

    def prepare_telescope_types(self, obj):
        return _prepare_telescope_types(obj)

    def prepare_camera_types(self, obj):
        return _prepare_camera_types(obj)

    def prepare_comments(self, obj):
        return _prepare_comments(obj)

    def prepare_is_commercial(self, obj):
        commercial_gear = CommercialGear.objects.filter(image = obj)
        return commercial_gear.count() > 0


site.register(Gear, GearIndex)
site.register(User, UserIndex)
site.register(Image, ImageIndex)
