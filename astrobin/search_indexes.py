import datetime
import logging
import sys
from functools import reduce

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db.models import Count, Q
from django.template.defaultfilters import striptags
from haystack.constants import Indexable
from haystack.fields import BooleanField, CharField, DateTimeField, FloatField, IntegerField, MultiValueField
from celery_haystack.indexes import CelerySearchIndex
from hitcount.models import HitCount
from precise_bbcode.templatetags.bbcode_tags import bbcode
from pybb.models import Post, Topic
from safedelete.models import SafeDeleteModel

from astrobin.enums.license import License
from astrobin.enums.moderator_decision import ModeratorDecision
from astrobin.models import DeepSky_Acquisition, GearUserInfo, Image, SolarSystem_Acquisition, Camera as LegacyCamera
from astrobin.services.utils_service import UtilsService
from astrobin_apps_equipment.models import Camera
from astrobin_apps_equipment.models.sensor_base_model import ColorOrMono
from astrobin_apps_images.services import ImageService
from astrobin_apps_iotd.services import IotdService
from astrobin_apps_platesolving.services import SolutionService
from astrobin_apps_users.services import UserService
from common.utils import get_segregated_reader_database
from nested_comments.models import NestedComment
from toggleproperties.models import ToggleProperty

logger = logging.getLogger(__name__)

PREPARED_FIELD_CACHE_EXPIRATION = 3600
PREPARED_MOON_PHASE_CACHE_KEY = 'search_index_prepared_moon_phase.%d'
PREPARED_VIEWS_CACHE_KEY = 'search_index_prepared_views.%d'
PREPARED_BOOKMARKS_CACHE_KEY = 'search_index_prepared_bookmarks.%d'
PREPARED_LIKES_CACHE_KEY = 'search_index_prepared_likes.%d'
PREPARED_COMMENTS_CACHE_KEY = 'search_index_prepared_comments.%d'
PREPARED_INTEGRATION_CACHE_KEY = 'search_index_prepared_integration.%d'


def _prepare_integration(obj):
    deep_sky_acquisitions = DeepSky_Acquisition.objects.using(get_segregated_reader_database()).filter(image=obj)
    solar_system_acquisition = None
    integration = 0

    try:
        solar_system_acquisition = SolarSystem_Acquisition.objects.get(image=obj)
    except (SolarSystem_Acquisition.DoesNotExist, SolarSystem_Acquisition.MultipleObjectsReturned):
        pass

    if deep_sky_acquisitions:
        for a in deep_sky_acquisitions:
            if a.duration and a.number:
                integration += (a.duration * a.number)
    elif solar_system_acquisition:
        integration = 0

    cache.set(PREPARED_INTEGRATION_CACHE_KEY % obj.pk, float(integration), PREPARED_FIELD_CACHE_EXPIRATION)
    return float(integration)


def _prepare_likes(obj):
    result = ToggleProperty.objects.toggleproperties_for_object("like", obj).count()
    cache.set(PREPARED_LIKES_CACHE_KEY % obj.pk, result, PREPARED_FIELD_CACHE_EXPIRATION)
    return result


def _prepare_bookmarks(obj):
    result = ToggleProperty.objects.toggleproperties_for_object("bookmark", obj).count()
    cache.set(PREPARED_BOOKMARKS_CACHE_KEY % obj.pk, result, PREPARED_FIELD_CACHE_EXPIRATION)
    return result


def _prepare_moon_phase(obj):
    from .moon import MoonPhase

    deep_sky_acquisitions = DeepSky_Acquisition.objects.using(get_segregated_reader_database()).filter(image=obj)
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

    result = sum(moon_illuminated_list) / float(len(moon_illuminated_list))
    cache.set(PREPARED_MOON_PHASE_CACHE_KEY % obj.pk, result, PREPARED_FIELD_CACHE_EXPIRATION)
    return result


def _prepare_first_acquisition_date(obj):
    deep_sky_acquisitions = DeepSky_Acquisition.objects.using(get_segregated_reader_database()).filter(image=obj)
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
    deep_sky_acquisitions = DeepSky_Acquisition.objects.using(get_segregated_reader_database()).filter(image=obj)
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
    try:
        result = HitCount.objects.get(object_pk=obj.pk, content_type__model=content_type).hits
    except Exception as e:
        result = 0

    cache.set(PREPARED_VIEWS_CACHE_KEY % obj.pk, result, PREPARED_FIELD_CACHE_EXPIRATION)
    return result


def _prepare_min_aperture(obj):
    value = 0

    for telescope in obj.imaging_telescopes.filter(aperture__isnull=False):
        if value == 0 or telescope.aperture < value:
            value = int(telescope.aperture)

    for telescope in obj.imaging_telescopes_2.filter(aperture__isnull=False):
        if value == 0 or telescope.aperture < value:
            value = int(telescope.aperture)

    return value


def _prepare_max_aperture(obj):
    import sys
    value = sys.maxsize

    for telescope in obj.imaging_telescopes.filter(aperture__isnull=False):
        if value == sys.maxsize or telescope.aperture > value:
            value = int(telescope.aperture)

    for telescope in obj.imaging_telescopes_2.filter(aperture__isnull=False):
        if value == sys.maxsize or telescope.aperture > value:
            value = int(telescope.aperture)

    return value


def _prepare_min_focal_length(obj):
    value = 0

    for telescope in obj.imaging_telescopes.filter(focal_length__isnull=False):
        if value == 0 or telescope.focal_length < value:
            value = int(telescope.focal_length)

    for telescope in obj.imaging_telescopes_2.filter(min_focal_length__isnull=False):
        if value == 0 or telescope.min_focal_length < value:
            value = int(telescope.min_focal_length)

    return value


def _prepare_max_focal_length(obj):
    import sys
    value = sys.maxsize

    for telescope in obj.imaging_telescopes.filter(focal_length__isnull=False):
        if value == sys.maxsize or telescope.focal_length > value:
            value = int(telescope.focal_length)

    for telescope in obj.imaging_telescopes_2.filter(max_focal_length__isnull=False):
        if value == sys.maxsize or telescope.max_focal_length > value:
            value = int(telescope.max_focal_length)

    return value


def _prepare_min_camera_pixel_size(obj):
    value = 0

    for camera in obj.imaging_cameras.filter(pixel_size__isnull=False):
        if value == 0 or camera.pixel_size < value:
            value = float(camera.pixel_size)

    for camera in obj.imaging_cameras_2.filter(sensor__isnull=False, sensor__pixel_size__isnull=False):
        if value == 0 or camera.sensor.pixel_size < value:
            value = float(camera.sensor.pixel_size)

    return value


def _prepare_max_camera_pixel_size(obj):
    import sys
    value = sys.maxsize

    for camera in obj.imaging_cameras.filter(pixel_size__isnull=False):
        if value == sys.maxsize or camera.pixel_size > value:
            value = float(camera.pixel_size)

    for camera in obj.imaging_cameras_2.filter(sensor__isnull=False, sensor__pixel_size__isnull=False):
        if value == sys.maxsize or camera.sensor.pixel_size > value:
            value = float(camera.sensor.pixel_size)

    return value


def _prepare_telescope_types(obj):
    return list(set([x.type for x in obj.imaging_telescopes.all()] + [x.type for x in obj.imaging_telescopes_2.all()]))


def _prepare_camera_types(obj):
    return list(set([x.type for x in obj.imaging_cameras.all()] + [x.type for x in obj.imaging_cameras_2.all()]))


def _prepare_comments(obj):
    ct = ContentType.objects.get(app_label='astrobin', model='image')
    result = NestedComment.objects.using(get_segregated_reader_database()).filter(
        content_type=ct,
        object_id=obj.id,
        deleted=False
    ).count()
    cache.set(PREPARED_COMMENTS_CACHE_KEY % obj.pk, result, PREPARED_FIELD_CACHE_EXPIRATION)
    return result


class UserIndex(CelerySearchIndex, Indexable):
    text = CharField(document=True, use_template=True)

    username = CharField(model_attr='username')
    exclude_from_competitions = BooleanField(model_attr='userprofile__exclude_from_competitions')

    avg_integration = FloatField()

    images = IntegerField()

    # Total likes of all user's images.
    likes = IntegerField()

    # Total likes given to images.
    likes_given = IntegerField()

    # Normalized likes (Image Index)
    normalized_likes = FloatField()

    # Total likes received on comments.
    comment_likes_received = IntegerField()

    # Total likes received on forum posts.
    forum_post_likes_received = IntegerField()

    # Total number of likes on all "likeable" elements that can be associated to a user.
    total_likes_received = IntegerField()

    # Index based on text content
    contribution_index = FloatField(model_attr='userprofile__contribution_index', null=True)

    # Number of followers
    followers = IntegerField()

    # Total user integration.
    integration = FloatField()

    # Average moon phase under which this user has operated.
    moon_phase = FloatField()

    # Total views from all images.
    views = IntegerField()

    # Number of bookmarks on own images
    bookmarks = IntegerField()

    # Comments received on on own images
    comments = IntegerField()

    comments_written = IntegerField()

    forum_posts = IntegerField()

    top_pick_nominations = IntegerField()

    top_picks = IntegerField()

    iotds = IntegerField()

    def index_queryset(self, using=None):
        return self.get_model().objects.annotate(
            num_images=Count(
                'image',
                filter=Q(image__moderator_decision=ModeratorDecision.APPROVED) & Q(image__deleted__isnull=False)
            ),
            num_posts=Count('posts', filter=Q(posts__on_moderation=False)),
        ).filter(
            Q(num_images__gt=0) | Q(num_posts__gt=0)
        )

    def get_model(self):
        return User

    def get_updated_field(self):
        return "userprofile__updated"

    def prepare_images(self, obj):
        return UserService(obj).get_public_images().count()

    def prepare_avg_integration(self, obj):
        integration = 0
        images = 0
        for i in UserService(obj).get_public_images():
            cached = cache.get(PREPARED_INTEGRATION_CACHE_KEY % i.pk)
            image_integration = cached if cached is not None else _prepare_integration(i)
            if image_integration:
                images += 1
                integration += image_integration

        return (integration / 3600.0) / images if images else 0

    def prepare_likes(self, obj):
        likes = 0
        for i in UserService(obj).get_public_images():
            cached = cache.get(PREPARED_LIKES_CACHE_KEY % i.pk)
            likes += cached if cached is not None else _prepare_likes(i)
        return likes

    def prepare_likes_given(self, obj):
        return ToggleProperty.objects.toggleproperties_for_model('like', Image, obj).count()


    def prepare_normalized_likes(self, obj):
        return obj.userprofile.image_index

    def prepare_comment_likes_received(self, obj):
        comments = NestedComment.objects.using(get_segregated_reader_database()).filter(author=obj)
        likes = 0
        for comment in comments.iterator():
            likes += ToggleProperty.objects.toggleproperties_for_object('like', comment).count()

        return likes

    def prepare_forum_post_likes_received(self, obj):
        posts = Post.objects.using(get_segregated_reader_database()).filter(user=obj)
        likes = 0
        for post in posts.iterator():
            likes += ToggleProperty.objects.toggleproperties_for_object('like', post).count()

        return likes

    def prepare_total_likes_received(self, obj):
        likes = self.prepared_data.get('likes')
        if likes is None:
            likes = self.prepare_likes(obj)

        comment_likes_received = self.prepared_data.get('comment_likes_received')
        if comment_likes_received is None:
            comment_likes_received = self.prepare_comment_likes_received(obj)

        forum_post_likes_received = self.prepared_data.get('forum_post_likes_received')
        if forum_post_likes_received is None:
            forum_post_likes_received = self.prepare_forum_post_likes_received(obj)

        return likes + comment_likes_received + forum_post_likes_received


    def prepare_followers(self, obj):
        return ToggleProperty.objects.filter(
            property_type="follow",
            content_type=ContentType.objects.get_for_model(User),
            object_id=obj.pk
        ).count()

    def prepare_integration(self, obj):
        integration = 0
        for i in UserService(obj).get_public_images():
            cached = cache.get(PREPARED_INTEGRATION_CACHE_KEY % i.pk)
            integration += cached if cached is not None else _prepare_integration(i)

        return integration / 3600.0

    def prepare_moon_phase(self, obj):
        l = []
        for i in UserService(obj).get_public_images():
            cached = cache.get(PREPARED_MOON_PHASE_CACHE_KEY % i.pk)
            l.append(cached if cached is not None else _prepare_moon_phase(i))
        if len(l) == 0:
            return 0
        return reduce(lambda x, y: x + y, l) / len(l)

    def prepare_views(self, obj):
        views = 0
        for i in UserService(obj).get_public_images():
            cached = cache.get(PREPARED_VIEWS_CACHE_KEY % i.pk)
            views += cached if cached is not None else _prepare_views(i, 'image')
        return views

    def prepare_bookmarks(self, obj):
        bookmarks = 0
        for i in UserService(obj).get_public_images():
            cached = cache.get(PREPARED_BOOKMARKS_CACHE_KEY % i.pk)
            bookmarks += cached if cached is not None else _prepare_bookmarks(i)
        return bookmarks

    def prepare_comments(self, obj):
        comments = 0
        for i in UserService(obj).get_public_images():
            cached = cache.get(PREPARED_COMMENTS_CACHE_KEY % i.pk)
            comments += cached if cached is not None else _prepare_comments(i)
        return comments

    def prepare_comments_written(self, obj):
        return NestedComment.objects.using(get_segregated_reader_database()).filter(author=obj, deleted=False).count()

    def prepare_forum_posts(self, obj):
        return Post.objects.using(get_segregated_reader_database()).filter(user=obj).count()

    def prepare_top_pick_nominations(self, obj):
        return IotdService().get_top_pick_nominations().filter(
            Q(image__user=obj) | Q(image__collaborators=obj)
        ).distinct().count()

    def prepare_top_picks(self, obj):
        return IotdService().get_top_picks().filter(
            Q(image__user=obj) | Q(image__collaborators=obj)
        ).distinct().count()

    def prepare_iotds(self, obj):
        return IotdService().get_iotds().filter(Q(image__user=obj) | Q(image__collaborators=obj)).distinct().count()


class ImageIndex(CelerySearchIndex, Indexable):
    text = CharField(document=True, use_template=True)

    object_id = CharField(model_attr='id')
    hash = CharField(null=True, model_attr='hash')
    title = CharField(model_attr='title')
    description = CharField(null=True)
    published = DateTimeField(model_attr='published')
    uploaded = DateTimeField(model_attr='uploaded')

    # Old DB
    imaging_telescopes = CharField()
    guiding_telescopes = CharField()
    mounts = CharField()
    imaging_cameras = CharField()
    guiding_cameras = CharField()

    all_sensors = CharField()  # Includes guiding and imaging
    imaging_sensors = CharField()
    guiding_sensors = CharField()
    all_sensors_id = CharField()
    imaging_sensors_id = CharField()
    guiding_sensors_id = CharField()

    all_cameras_2 = CharField()  # Includes guiding and imaging
    imaging_cameras_2 = CharField()
    guiding_cameras_2 = CharField()
    all_cameras_2_id = CharField()
    imaging_cameras_2_id = CharField()
    guiding_cameras_2_id = CharField()

    all_telescopes_2 = CharField()  # Includes guiding and imaging
    imaging_telescopes_2 = CharField()
    guiding_telescopes_2 = CharField()
    all_telescopes_2_id = CharField()
    imaging_telescopes_2_id = CharField()
    guiding_telescopes_2_id = CharField()

    mounts_2 = CharField()
    mounts_2_id = CharField()

    filters_2 = CharField()
    filters_2_id = CharField()
    filter_types = MultiValueField()

    accessories_2 = CharField()
    accessories_2_id = CharField()

    software_2 = CharField()
    software_2_id = CharField()

    has_modified_camera = BooleanField()
    has_color_camera = BooleanField()
    has_mono_camera = BooleanField()

    coord_ra_min = FloatField()
    coord_ra_max = FloatField()
    coord_dec_min = FloatField()
    coord_dec_max = FloatField()
    pixel_scale = FloatField()
    field_radius = FloatField()
    countries = CharField()

    animated = BooleanField(model_attr='animated')
    video = BooleanField()
    video_url = CharField()
    loop_video = BooleanField()

    likes = IntegerField()
    liked_by = MultiValueField()
    integration = FloatField()
    moon_phase = FloatField()
    first_acquisition_date = DateTimeField()
    last_acquisition_date = DateTimeField()
    acquisition_months = MultiValueField()
    views = IntegerField()
    w = IntegerField(model_attr='w', null=True)
    h = IntegerField(model_attr='h', null=True)
    pixel_count = IntegerField(null=True)
    size = IntegerField(model_attr='uploader_upload_length', null=True)

    solar_system_main_subject_char = CharField(model_attr='solar_system_main_subject', null=True)

    is_deep_sky = BooleanField()
    is_solar_system = BooleanField()
    is_sun = BooleanField()
    is_moon = BooleanField()
    is_planets = BooleanField()
    is_comets = BooleanField()
    constellation = CharField()

    is_iotd = BooleanField()
    is_top_pick = BooleanField()
    is_top_pick_nomination = BooleanField()

    license = IntegerField()
    license_name = CharField()

    min_aperture = IntegerField()
    max_aperture = IntegerField()

    min_telescope_weight = FloatField()
    max_telescope_weight = FloatField()

    min_mount_weight = FloatField()
    max_mount_weight = FloatField()

    min_mount_max_payload = FloatField()
    max_mount_max_payload = FloatField()

    min_focal_length = IntegerField()
    max_focal_length = IntegerField()

    min_camera_pixel_size = FloatField()
    max_camera_pixel_size = FloatField()

    bookmarks = IntegerField()
    bookmarked_by = MultiValueField()

    telescope_types = MultiValueField()
    camera_types = MultiValueField()

    comments = IntegerField()

    subject_type_char = CharField(model_attr='subject_type')

    acquisition_type = CharField(model_attr='acquisition_type')

    data_source = CharField(model_attr='data_source')

    remote_source = CharField(model_attr='remote_source', null=True)

    groups = CharField()

    username = CharField(model_attr='user__username')
    user_id = IntegerField(model_attr='user_id')
    user_display_name = CharField()

    objects_in_field = CharField()

    bortle_scale = FloatField()

    gallery_thumbnail = CharField()

    user_followed_by = MultiValueField()

    def index_queryset(self, using=None):
        return self.get_model().objects.using(get_segregated_reader_database()).filter(
            moderator_decision=ModeratorDecision.APPROVED
        )

    def should_update(self, instance, **kwargs):
        return not instance.is_wip and instance.moderator_decision == ModeratorDecision.APPROVED

    def get_model(self):
        return Image

    def get_updated_field(self):
        return 'updated'

    def prepare_description(self, obj):
        logger.info('Updating ImageIndex: %d' % obj.pk)
        if obj.description_bbcode:
            return striptags(bbcode(obj.description_bbcode))
        return striptags(obj.description)

    ###################################################################################################################
    ###################################################################################################################
    ### OLD DB                                                                                                      ###
    ###################################################################################################################
    ###################################################################################################################

    def prepare_imaging_telescopes(self, obj):
        return [
            f"{x.get('make')} {x.get('name')}" for x in obj.imaging_telescopes.all().values('make', 'name')
        ]

    def prepare_guiding_telescopes(self, obj):
        return [f"{x.get('make')} {x.get('name')}" for x in obj.guiding_telescopes.all().values('make', 'name')]

    def prepare_mounts(self, obj):
        return [f"{x.get('make')} {x.get('name')}" for x in obj.mounts.all().values('make', 'name')]

    def prepare_imaging_cameras(self, obj):
        return [
            f"{x.get('make')} {x.get('name')}" for x in obj.imaging_cameras.all().values('make', 'name', 'type')
        ]

    def prepare_guiding_cameras(self, obj):
        return [f"{x}" for x in obj.guiding_cameras.all()]

    ###################################################################################################################
    ###################################################################################################################
    ### NEW DB                                                                                                      ###
    ###################################################################################################################
    ###################################################################################################################

    def prepare_imaging_sensors(self, obj):
        return list(set([f"{x.sensor}" for x in obj.imaging_cameras_2.all() if x.sensor]))

    def prepare_guiding_sensors(self, obj):
        return list(set([f"{x.sensor}" for x in obj.guiding_cameras_2.all() if x.sensor]))

    def prepare_all_sensors(self, obj):
        return list(set(self.prepare_imaging_sensors(obj) + self.prepare_guiding_sensors(obj)))

    def prepare_imaging_sensors_id(self, obj):
        return list(set([f"{x.sensor.id}" for x in obj.imaging_cameras_2.all() if x.sensor]))

    def prepare_guiding_sensors_id(self, obj):
        return list(set([f"{x.sensor.id}" for x in obj.guiding_cameras_2.all() if x.sensor]))

    def prepare_all_sensors_id(self, obj):
        return list(set(self.prepare_imaging_sensors_id(obj) + self.prepare_guiding_sensors_id(obj)))

    ###################################################################################################################

    def prepare_imaging_telescopes_2(self, obj):
        return [f"{x}" for x in obj.imaging_telescopes_2.all()]

    def prepare_guiding_telescopes_2(self, obj):
        return [f"{x}" for x in obj.guiding_telescopes_2.all()]

    def prepare_all_telescopes_2(self, obj):
        return list(set(self.prepare_imaging_telescopes_2(obj) + self.prepare_guiding_telescopes_2(obj)))

    def prepare_imaging_telescopes_2_id(self, obj):
        return [f"{x.id}" for x in obj.imaging_telescopes_2.all()]

    def prepare_guiding_telescopes_2_id(self, obj):
        return [f"{x.id}" for x in obj.guiding_telescopes_2.all()]

    def prepare_all_telescopes_2_id(self, obj):
        return list(set(self.prepare_imaging_telescopes_2_id(obj) + self.prepare_guiding_telescopes_2_id(obj)))

    ###################################################################################################################

    def prepare_imaging_cameras_2(self, obj):
        return [f"{x}" for x in obj.imaging_cameras_2.all()]

    def prepare_guiding_cameras_2(self, obj):
        return [f"{x}" for x in obj.guiding_cameras_2.all()]

    def prepare_all_cameras_2(self, obj):
        return list(set(self.prepare_imaging_cameras_2(obj) + self.prepare_guiding_cameras_2(obj)))

    def prepare_imaging_cameras_2_id(self, obj):
        return [f"{x.id}" for x in obj.imaging_cameras_2.all()]

    def prepare_guiding_cameras_2_id(self, obj):
        return [f"{x.id}" for x in obj.guiding_cameras_2.all()]

    def prepare_all_cameras_2_id(self, obj):
        return list(set(self.prepare_imaging_cameras_2_id(obj) + self.prepare_guiding_cameras_2_id(obj)))

    ###################################################################################################################

    def prepare_mounts_2(self, obj):
        return [f"{x}" for x in obj.mounts_2.all()]

    def prepare_mounts_2_id(self, obj):
        return [f"{x.id}" for x in obj.mounts_2.all()]

    ###################################################################################################################

    def prepare_filters_2(self, obj):
        return [f"{x}" for x in obj.filters_2.all()]

    def prepare_filters_2_id(self, obj):
        return [f"{x.id}" for x in obj.filters_2.all()]

    def prepare_filter_types(self, obj):
        return [f"{x.type}" for x in obj.filters_2.all()]

    ###################################################################################################################

    def prepare_accessories_2(self, obj):
        return [f"{x}" for x in obj.accessories_2.all()]

    def prepare_accessories_2_id(self, obj):
        return [f"{x.id}" for x in obj.accessories_2.all()]

    ###################################################################################################################

    def prepare_software_2(self, obj):
        return [f"{x}" for x in obj.software_2.all()]

    def prepare_software_2_id(self, obj):
        return [f"{x.id}" for x in obj.software_2.all()]

    ###################################################################################################################

    def prepare_has_modified_camera(self, obj):
        legacy_camera: LegacyCamera
        for legacy_camera in obj.imaging_cameras.all().iterator():
            try:
                info: GearUserInfo = GearUserInfo.objects.get(gear=legacy_camera, user=obj.user)
                if info.modded:
                    return True
            except GearUserInfo.DoesNotExist:
                continue
        camera: Camera
        for camera in obj.imaging_cameras_2.all().iterator():
            if camera.modified:
                return True

        return False

    def prepare_has_color_camera(self, obj):
        camera: Camera
        for camera in obj.imaging_cameras_2.all().iterator():
            if camera.sensor and camera.sensor.color_or_mono == ColorOrMono.COLOR.value:
                return True

        return False

    def prepare_has_mono_camera(self, obj):
        camera: Camera
        for camera in obj.imaging_cameras_2.all().iterator():
            if camera.sensor and camera.sensor.color_or_mono == ColorOrMono.MONO.value:
                return True

        return False

    def prepare_min_camera_pixel_size(self, obj):
        return _prepare_min_camera_pixel_size(obj)

    def prepare_max_camera_pixel_size(self, obj):
        return _prepare_max_camera_pixel_size(obj)

    def prepare_min_aperture(self, obj):
        return _prepare_min_aperture(obj)

    def prepare_max_aperture(self, obj):
        return _prepare_max_aperture(obj)

    def prepare_min_telescope_weight(self, obj):
        value = 0

        for telescope in obj.imaging_telescopes_2.filter(weight__isnull=False):
            if value == 0 or telescope.weight < value:
                value = telescope.weight

        return value

    def prepare_max_telescope_weight(self, obj):
        value = sys.maxsize

        for telescope in obj.imaging_telescopes_2.filter(weight__isnull=False):
            if value == sys.maxsize or telescope.weight > value:
                value = int(telescope.weight)

        return value

    def prepare_min_mount_weight(self, obj):
        value = 0

        for mount in obj.mounts_2.filter(weight__isnull=False):
            if value == 0 or mount.weight < value:
                value = mount.weight

        return value

    def prepare_max_mount_weight(self, obj):
        value = sys.maxsize

        for mount in obj.mounts_2.filter(weight__isnull=False):
            if value == sys.maxsize or mount.weight > value:
                value = int(mount.weight)

        return value

    def prepare_min_mount_max_payload(self, obj):
        value = 0

        for mount in obj.mounts.filter(max_payload__isnull=False):
            if value == 0 or mount.max_payload < value:
                value = mount.max_payload

        for mount in obj.mounts_2.filter(max_payload__isnull=False):
            if value == 0 or mount.max_payload < value:
                value = mount.max_payload

        return value

    def prepare_max_mount_max_payload(self, obj):
        value = sys.maxsize

        for mount in obj.mounts.filter(max_payload__isnull=False):
            if value == sys.maxsize or mount.max_payload > value:
                value = int(mount.max_payload)

        for mount in obj.mounts_2.filter(max_payload__isnull=False):
            if value == sys.maxsize or mount.max_payload > value:
                value = int(mount.max_payload)

        return value

    def prepare_min_focal_length(self, obj):
        return _prepare_min_focal_length(obj)

    def prepare_max_focal_length(self, obj):
        return _prepare_max_focal_length(obj)

    def prepare_coord_ra_min(self, obj):
        if obj.solution is not None and obj.solution.ra is not None and obj.solution.radius is not None:
            return obj.solution.ra - obj.solution.radius
        return None

    def prepare_coord_ra_max(self, obj):
        if obj.solution is not None and obj.solution.ra is not None and obj.solution.radius is not None:
            return obj.solution.ra + obj.solution.radius
        return None

    def prepare_coord_dec_min(self, obj):
        if obj.solution is not None and obj.solution.dec is not None and obj.solution.radius is not None:
            return obj.solution.dec - obj.solution.radius
        return None

    def prepare_coord_dec_max(self, obj):
        if obj.solution is not None and obj.solution.dec is not None and obj.solution.radius is not None:
            return obj.solution.dec + obj.solution.radius
        return None

    def prepare_pixel_scale(self, obj):
        return obj.solution.pixscale if obj.solution else None

    def prepare_field_radius(self, obj):
        return obj.solution.radius if obj.solution else None

    def prepare_video(self, obj):
        return obj.video_file.name is not None and obj.video_file.name != ''

    def prepare_video_url(self, obj):
        return obj.encoded_video_file.url\
            if (obj.encoded_video_file.name is not None and
                obj.encoded_video_file.name != '')\
            else None

    def prepare_loop_video(self, obj):
        return obj.loop_video if obj.loop_video else False

    def prepare_likes(self, obj):
        return _prepare_likes(obj)

    def prepare_liked_by(self, obj):
        likes = ToggleProperty.objects.toggleproperties_for_object("like", obj).filter(user__isnull=False)
        return [x.user.pk for x in likes.all()]

    def prepare_integration(self, obj):
        return _prepare_integration(obj)

    def prepare_moon_phase(self, obj):
        return _prepare_moon_phase(obj)

    def prepare_first_acquisition_date(self, obj):
        return _prepare_first_acquisition_date(obj)

    def prepare_last_acquisition_date(self, obj):
        return _prepare_last_acquisition_date(obj)

    def prepare_acquisition_months(self, obj):
        deep_sky_acquisitions = DeepSky_Acquisition.objects.using(get_segregated_reader_database()).filter(
            image=obj, date__isnull=False
        )

        if deep_sky_acquisitions.exists():
            return list(set([x.date.strftime('%b') for x in deep_sky_acquisitions.all()]))
        else:
            try:
                solar_system_acquisition = SolarSystem_Acquisition.objects.get(image=obj)
                if solar_system_acquisition.date:
                    return [solar_system_acquisition.date.strftime('%b')]
                else:
                    return None
            except SolarSystem_Acquisition.DoesNotExist:
                return None

        return None

    def prepare_views(self, obj):
        return _prepare_views(obj, 'image')

    def prepare_pixel_count(self, obj):
        if obj.w and obj.h:
            return obj.w * obj.h
        return None

    def prepare_license(self, obj):
        return License.to_deprecated_integer(obj.license)

    def prepare_license_name(self, obj):
        return obj.license

    def prepare_bookmarks(self, obj):
        return _prepare_bookmarks(obj)

    def prepare_bookmarked_by(self, obj):
        bookmarks = ToggleProperty.objects.toggleproperties_for_object("bookmark", obj)
        return [x.user.pk for x in bookmarks.all()]

    def prepare_constellation(self, obj):
        constellation = ImageService.get_constellation(obj.solution)
        # Escape with __ because And (Andromeda) is not searchable, due to it being the same word as the AND operator.
        return "__%s__" % constellation.get('abbreviation') if constellation else None

    def prepare_telescope_types(self, obj):
        return _prepare_telescope_types(obj)

    def prepare_camera_types(self, obj):
        return _prepare_camera_types(obj)

    def prepare_comments(self, obj):
        return _prepare_comments(obj)

    def prepare_is_iotd(self, obj):
        return IotdService().is_iotd(obj)

    def prepare_is_top_pick(self, obj):
        return IotdService().is_top_pick(obj) and not IotdService().is_iotd(obj)

    def prepare_is_top_pick_nomination(self, obj):
        return IotdService().is_top_pick_nomination(obj) and \
            not IotdService().is_top_pick(obj) and \
            not IotdService().is_iotd(obj)

    def prepare_objects_in_field(self, obj):
        if not obj.solution or not obj.solution.objects_in_field:
            return None

        objects = ' '.join(SolutionService(obj.solution).duplicate_objects_in_field_by_catalog_space()).strip()

        for x in obj.solution.objects_in_field.split(','):
            synonyms = UtilsService.get_search_synonyms_text(x.strip())
            if synonyms:
                objects = f'{objects} {" ".join(synonyms.split(","))}'.strip()

        return objects


    def prepare_countries(self, obj):
        # Escape with __ because for whatever reason some country codes don't work, including IT.
        return ' '.join(['__%s__' % x.country for x in obj.locations.all() if x.country]).strip() or None

    def prepare_groups(self, obj):
        return ' '.join([f'__{x.pk}__' for x in obj.part_of_group_set.all()]).strip() or None

    def prepare_bortle_scale(self, obj):
        deep_sky_acquisitions = DeepSky_Acquisition.objects.using(get_segregated_reader_database()).filter(
            image=obj, bortle__isnull=False
        )

        if deep_sky_acquisitions.exists():
            return sum([float(x.bortle) for x in deep_sky_acquisitions]) / float(deep_sky_acquisitions.count())

        return None

    def prepare_gallery_thumbnail(self, obj: Image):
        return obj.thumbnail('gallery', 'final', sync=True)

    def prepare_user_followed_by(self, obj: Image):
        follows = ToggleProperty.objects.toggleproperties_for_object("follow", obj.user)
        return [x.user.pk for x in follows.all()]

    def prapare_user_display_name(self, obj: Image):
        return obj.user.userprofile.get_display_name()


class NestedCommentIndex(CelerySearchIndex, Indexable):
    text = CharField(document=True, use_template=True)
    created = DateTimeField(model_attr='created')
    updated = DateTimeField(model_attr='updated')

    def get_model(self):
        return NestedComment

    def index_queryset(self, using=None):
        return self.get_model().objects.using(get_segregated_reader_database()).filter(deleted=False)

    def should_update(self, instance, **kwargs):
        if instance.deleted:
            return False

        if issubclass(type(instance.content_object), SafeDeleteModel):
            if instance.content_object.deleted:
                return False

        if isinstance(instance.content_object, Image):
            if (
                    instance.content_object.is_wip or
                    instance.content_object.moderator_decision != ModeratorDecision.APPROVED
            ):
                return False

        return True

    def get_updated_field(self):
        return "updated"


class ForumTopicIndex(CelerySearchIndex, Indexable):
    text = CharField(document=True, use_template=True)
    created = DateTimeField(model_attr='created')
    updated = DateTimeField(model_attr='updated', null=True)

    def get_model(self):
        return Topic

    def index_queryset(self, using=None):
        return self.get_model().objects.using(get_segregated_reader_database()).filter(
            forum__group__isnull=True,
            on_moderation=False,
            forum__hidden=False,
            forum__category__hidden=False
        )

    def should_update(self, instance, **kwargs):
        return (
                not hasattr(instance.forum, 'group') and
                not instance.on_moderation and
                not instance.forum.hidden and
                not instance.forum.category.hidden
        )

    def get_updated_field(self):
        return "updated"


class ForumPostIndex(CelerySearchIndex, Indexable):
    text = CharField(document=True, use_template=True)
    created = DateTimeField(model_attr='created')
    updated = DateTimeField(model_attr='updated', null=True)
    topic_id = IntegerField(model_attr='topic__pk', null=False)

    def get_model(self):
        return Post

    def index_queryset(self, using=None):
        return self.get_model().objects.using(get_segregated_reader_database()).filter(
            topic__forum__group__isnull=True,
            on_moderation=False,
            topic__forum__hidden=False,
            topic__forum__category__hidden=False
        )

    def should_update(self, instance, **kwargs):
        return (
                not hasattr(instance.topic.forum, 'group') and
                not instance.on_moderation and
                not instance.topic.forum.hidden and
                not instance.topic.forum.category.hidden
        )

    def get_updated_field(self):
        return "updated"
