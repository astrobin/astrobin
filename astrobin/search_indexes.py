import datetime
import logging

from celery_haystack.indexes import CelerySearchIndex
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from haystack.constants import Indexable
from haystack.fields import CharField, IntegerField, FloatField, DateTimeField, BooleanField, MultiValueField
from hitcount.models import HitCount
from pybb.models import Post, Topic

from astrobin.enums import SubjectType, SolarSystemSubject
from astrobin.models import CommercialGear
from astrobin.models import DeepSky_Acquisition
from astrobin.models import Image
from astrobin.models import SolarSystem_Acquisition
from nested_comments.models import NestedComment
from toggleproperties.models import ToggleProperty

log = logging.getLogger('apps')


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


def _prepare_bookmarks(obj):
    return ToggleProperty.objects.toggleproperties_for_object("bookmark", obj).count()


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

    return date if date else datetime.date.min


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

    return date if date else datetime.date.min


def _prepare_views(obj, content_type):
    views = 0
    try:
        views = HitCount.objects.get(object_pk=obj.pk, content_type__name=content_type).hits
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
    ct = ContentType.objects.get(app_label='astrobin', model='image')
    return NestedComment.objects.filter(
        content_type=ct,
        object_id=obj.id,
        deleted=False).count()


def _6m_ago():
    return datetime.datetime.now() - datetime.timedelta(183)


def _1y_ago():
    return datetime.datetime.now() - datetime.timedelta(365)


class UserIndex(CelerySearchIndex, Indexable):
    text = CharField(document=True, use_template=True)
    images_6m = IntegerField()
    images_1y = IntegerField()
    images = IntegerField()
    avg_integration = FloatField()

    # Total likes of all user's images.
    likes = IntegerField()

    # Total likes of all user's images.
    average_likes_6m = FloatField()
    average_likes_1y = FloatField()
    average_likes = FloatField()

    # Normalized likes (best images only)
    normalized_likes_6m = FloatField()
    normalized_likes_1y = FloatField()
    normalized_likes = FloatField()

    # Number of followers
    followers_6m = IntegerField()
    followers_1y = IntegerField()
    followers = IntegerField()

    # Total user ingegration.
    integration_6m = FloatField()
    integration_1y = FloatField()
    integration = FloatField()

    # Average moon phase under which this user has operated.
    moon_phase = FloatField()

    # Total views from all images.
    views = IntegerField()

    # Number of bookmarks on own images
    bookmarks = IntegerField()

    comments = IntegerField()
    comments_written = IntegerField()

    username = CharField(model_attr='username')

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def get_model(self):
        return User

    def get_updated_field(self):
        return "userprofile__updated"

    def prepare_images_6m(self, obj):
        # Logging here just because it's the first "prepare" function.
        log.debug("Indexing user %s: %d" % (obj.__class__.__name__, obj.pk))

        return Image.objects.filter(user=obj).filter(
            uploaded__gte=_6m_ago()).count()

    def prepare_images_1y(self, obj):
        return Image.objects.filter(user=obj).filter(
            uploaded__gte=_1y_ago()).count()

    def prepare_images(self, obj):
        return Image.objects.filter(user=obj).count()

    def prepare_avg_integration(self, obj):
        integration = 0
        images = 0
        for i in Image.objects.filter(user=obj):
            image_integration = _get_integration(i)
            if image_integration:
                images += 1
                integration += image_integration

        return (integration / 3600.0) / images if images else 0

    def prepare_likes(self, obj):
        likes = 0
        for i in Image.objects.filter(user=obj):
            likes += ToggleProperty.objects.toggleproperties_for_object("like", i).count()
        return likes

    def prepare_likes_6m(self, obj):
        likes = 0
        for i in Image.objects.filter(user=obj, uploaded__gte=_6m_ago()):
            likes += ToggleProperty.objects.toggleproperties_for_object("like", i).count()
        return likes

    def prepare_likes_1y(self, obj):
        likes = 0
        for i in Image.objects.filter(user=obj, uploaded__gte=_1y_ago()):
            likes += ToggleProperty.objects.toggleproperties_for_object("like", i).count()
        return likes

    def prepare_average_likes_6m(self, obj):
        likes = self.prepare_likes_6m(obj)
        images = Image.objects.filter(user=obj, uploaded__gte=_6m_ago()).count()

        return likes / float(images) if images > 0 else 0

    def prepare_average_likes_1y(self, obj):
        likes = self.prepare_likes_1y(obj)
        images = Image.objects.filter(user=obj, uploaded__gte=_1y_ago()).count()

        return likes / float(images) if images > 0 else 0

    def prepare_average_likes(self, obj):
        likes = self.prepare_likes(obj)
        images = self.prepare_images(obj)

        return likes / float(images) if images > 0 else 0

    def prepare_normalized_likes_6m(self, obj):
        def average(values):
            if len(values):
                return sum(values) / float(len(values))
            return 0

        def index(values):
            import math
            return average(values) * math.log(len(values) + 1, 10)

        avg = self.prepare_average_likes_6m(obj)
        norm = []

        for i in Image.objects.filter(user=obj).filter(uploaded__gte=_6m_ago()):
            likes = i.likes()
            if likes >= avg:
                norm.append(likes)

        if len(norm) == 0:
            return 0

        return index(norm)

    def prepare_normalized_likes_1y(self, obj):
        def average(values):
            if len(values):
                return sum(values) / float(len(values))
            return 0

        def index(values):
            import math
            return average(values) * math.log(len(values) + 1, 10)

        avg = self.prepare_average_likes_1y(obj)
        norm = []

        for i in Image.objects.filter(user=obj).filter(uploaded__gte=_1y_ago()):
            likes = i.likes()
            if likes >= avg:
                norm.append(likes)

        if len(norm) == 0:
            return 0

        return index(norm)

    def prepare_normalized_likes(self, obj):
        def average(values):
            if len(values):
                return sum(values) / float(len(values))
            return 0

        def index(values):
            import math
            return average(values) * math.log(len(values) + 1, 10)

        avg = self.prepare_average_likes(obj)
        norm = []

        for i in Image.objects.filter(user=obj):
            likes = i.likes()
            if likes >= avg:
                norm.append(likes)

        if len(norm) == 0:
            return 0

        return index(norm)

    def prepare_followers_6m(self, obj):
        return ToggleProperty.objects.filter(
            property_type="follow",
            content_type=ContentType.objects.get_for_model(User),
            object_id=obj.pk
        ).filter(created_on__gte=_6m_ago()).count()

    def prepare_followers_1y(self, obj):
        return ToggleProperty.objects.filter(
            property_type="follow",
            content_type=ContentType.objects.get_for_model(User),
            object_id=obj.pk
        ).filter(created_on__gte=_1y_ago()).count()

    def prepare_followers(self, obj):
        return ToggleProperty.objects.filter(
            property_type="follow",
            content_type=ContentType.objects.get_for_model(User),
            object_id=obj.pk
        ).count()

    def prepare_integration_6m(self, obj):
        integration = 0
        for i in Image.objects.filter(user=obj, uploaded__gte=_6m_ago()):
            integration += _get_integration(i)

        return integration / 3600.0

    def prepare_integration_1y(self, obj):
        integration = 0
        for i in Image.objects.filter(user=obj, uploaded__gte=_1y_ago()):
            integration += _get_integration(i)

        return integration / 3600.0

    def prepare_integration(self, obj):
        integration = 0
        for i in Image.objects.filter(user=obj):
            integration += _get_integration(i)

        return integration / 3600.0

    def prepare_moon_phase(self, obj):
        l = []
        for i in Image.objects.filter(user=obj):
            l.append(_prepare_moon_phase(i))
        if len(l) == 0:
            return 0
        return reduce(lambda x, y: x + y, l) / len(l)

    def prepare_views(self, obj):
        views = 0
        for i in Image.objects.filter(user=obj):
            views += _prepare_views(i, 'image')
        return views

    def prepare_bookmarks(self, obj):
        bookmarks = 0
        for i in Image.objects.filter(user=obj):
            bookmarks += _prepare_bookmarks(i)
        return bookmarks

    def prepare_comments(self, obj):
        comments = 0
        for i in Image.objects.filter(user=obj):
            comments += _prepare_comments(i)
        return comments

    def prepare_comments_written(self, obj):
        return NestedComment.objects.filter(author=obj, deleted=False).count()


class ImageIndex(CelerySearchIndex, Indexable):
    text = CharField(document=True, use_template=True)

    title = CharField(model_attr='title')
    description = CharField(model_attr='description', null=True)
    published = DateTimeField(model_attr='published')
    uploaded = DateTimeField(model_attr='uploaded')
    imaging_telescopes = CharField()
    guiding_telescopes = CharField()
    mounts = CharField()
    imaging_cameras = CharField()
    guiding_cameras = CharField()
    pixel_scale = FloatField()
    field_radius = FloatField()
    countries = CharField()

    animated = BooleanField(model_attr='animated')

    likes = IntegerField()
    integration = FloatField()
    moon_phase = FloatField()
    first_acquisition_date = DateTimeField()
    last_acquisition_date = DateTimeField()
    views = IntegerField()

    solar_system_main_subject = IntegerField(null=True)
    solar_system_main_subject_char = CharField(model_attr='solar_system_main_subject', null=True)

    is_deep_sky = BooleanField()
    is_solar_system = BooleanField()
    is_sun = BooleanField()
    is_moon = BooleanField()
    is_planets = BooleanField()
    is_comets = BooleanField()

    is_iotd = BooleanField()
    is_top_pick = BooleanField()

    license = IntegerField(model_attr='license')

    min_aperture = IntegerField()
    max_aperture = IntegerField()

    min_pixel_size = IntegerField()
    max_pixel_size = IntegerField()

    bookmarks = IntegerField()

    telescope_types = MultiValueField()
    camera_types = MultiValueField()

    comments = IntegerField()

    is_commercial = BooleanField()

    subject_type = IntegerField()
    subject_type_char = CharField(model_attr='subject_type')

    acquisition_type = CharField(model_attr='acquisition_type')

    data_source = CharField(model_attr='data_source')

    remote_source = CharField(model_attr='remote_source', null=True)

    username = CharField(model_attr='user__username')

    objects_in_field = CharField()

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(moderator_decision=1).exclude(corrupted=True)

    def get_model(self):
        return Image

    def get_updated_field(self):
        return "updated"

    def prepare_imaging_telescopes(self, obj):
        # Logging here just because it's the first "prepare" function.
        log.debug("Indexing image %s: %d" % (obj.__class__.__name__, obj.pk))

        return ["%s, %s" % (x.get("make"), x.get("name")) for x in obj.imaging_telescopes.all().values('make', 'name')]

    def prepare_guiding_telescopes(self, obj):
        return ["%s, %s" % (x.get("make"), x.get("name")) for x in obj.guiding_telescopes.all().values('make', 'name')]

    def prepare_mounts(self, obj):
        return ["%s, %s" % (x.get("make"), x.get("name")) for x in obj.mounts.all().values('make', 'name')]

    def prepare_imaging_cameras(self, obj):
        return ["%s, %s" % (x.get("make"), x.get("name")) for x in obj.imaging_cameras.all().values('make', 'name')]

    def prepare_guiding_cameras(self, obj):
        return ["%s, %s" % (x.get("make"), x.get("name")) for x in obj.guiding_cameras.all().values('make', 'name')]

    def prepare_pixel_scale(self, obj):
        return obj.solution.pixscale if obj.solution else None

    def prepare_field_radius(self, obj):
        return obj.solution.radius if obj.solution else None

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

    def prepare_bookmarks(self, obj):
        return _prepare_bookmarks(obj)

    def prepare_telescope_types(self, obj):
        return _prepare_telescope_types(obj)

    def prepare_camera_types(self, obj):
        return _prepare_camera_types(obj)

    def prepare_comments(self, obj):
        return _prepare_comments(obj)

    def prepare_is_commercial(self, obj):
        commercial_gear = CommercialGear.objects.filter(image=obj)
        return commercial_gear.count() > 0

    def prepare_is_iotd(self, obj):
        return hasattr(obj, 'iotd')

    def prepare_is_top_pick(self, obj):
        return obj.iotdvote_set.count() > 0 and not hasattr(obj, 'iotd')

    def prepare_objects_in_field(self, obj):
        return obj.solution.objects_in_field if obj.solution else None

    def prepare_countries(self, obj):
        return ' '.join([x.country for x in obj.locations.all() if x.country])

    def prepare_subject_type(self, obj):
        if obj.subject_type == SubjectType.DEEP_SKY:
            return 100
        if obj.subject_type == SubjectType.SOLAR_SYSTEM:
            return 200
        if obj.subject_type == SubjectType.WIDE_FIELD:
            return 300
        if obj.subject_type == SubjectType.STAR_TRAILS:
            return 400
        if obj.subject_type == SubjectType.NORTHERN_LIGHTS:
            return 450
        if obj.subject_type == SubjectType.GEAR:
            return 500
        if obj.subject_type == SubjectType.OTHER:
            return 600

        return 0

    def prepare_solar_system_main_subject(self, obj):
        if obj.solar_system_main_subject == SolarSystemSubject.SUN:
            return 0
        if obj.solar_system_main_subject == SolarSystemSubject.MOON:
            return 1
        if obj.solar_system_main_subject == SolarSystemSubject.MERCURY:
            return 2
        if obj.solar_system_main_subject == SolarSystemSubject.VENUS:
            return 3
        if obj.solar_system_main_subject == SolarSystemSubject.MARS:
            return 4
        if obj.solar_system_main_subject == SolarSystemSubject.JUPITER:
            return 5
        if obj.solar_system_main_subject == SolarSystemSubject.SATURN:
            return 6
        if obj.solar_system_main_subject == SolarSystemSubject.URANUS:
            return 7
        if obj.solar_system_main_subject == SolarSystemSubject.NEPTUNE:
            return 8
        if obj.solar_system_main_subject == SolarSystemSubject.MINOR_PLANET:
            return 9
        if obj.solar_system_main_subject == SolarSystemSubject.COMET:
            return 10
        if obj.solar_system_main_subject == SolarSystemSubject.OTHER:
            return 11

        return None


class NestedCommentIndex(CelerySearchIndex, Indexable):
    text = CharField(document=True, use_template=True)
    created = DateTimeField(model_attr='created')
    updated = DateTimeField(model_attr='updated')

    def get_model(self):
        return NestedComment

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(deleted=False, image__deleted=None)


class ForumTopicIndex(CelerySearchIndex, Indexable):
    text = CharField(document=True, use_template=True)
    created = DateTimeField(model_attr='created')
    updated = DateTimeField(model_attr='updated', null=True)

    def get_model(self):
        return Topic

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(on_moderation=False)


class ForumPostIndex(CelerySearchIndex, Indexable):
    text = CharField(document=True, use_template=True)
    created = DateTimeField(model_attr='created')
    updated = DateTimeField(model_attr='updated', null=True)

    def get_model(self):
        return Post

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(on_moderation=False)
