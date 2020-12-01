import datetime

from celery_haystack.indexes import CelerySearchIndex
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db.models.functions import Length
from haystack.constants import Indexable
from haystack.fields import CharField, IntegerField, FloatField, DateTimeField, BooleanField, MultiValueField
from hitcount.models import HitCount
from pybb.models import Post, Topic

from astrobin.models import DeepSky_Acquisition
from astrobin.models import Image
from astrobin.models import SolarSystem_Acquisition
from astrobin_apps_iotd.services import IotdService
from nested_comments.models import NestedComment
from toggleproperties.models import ToggleProperty

PREPARED_FIELD_CACHE_EXPIRATION = 3600
PREPARED_MOON_PHASE_CACHE_KEY = 'search_index_prepared_moon_phase.%d'
PREPARED_VIEWS_CACHE_KEY = 'search_index_prepared_views.%d'
PREPARED_BOOKMARKS_CACHE_KEY = 'search_index_prepared_bookmarks.%d'
PREPARED_LIKES_CACHE_KEY = 'search_index_prepared_likes.%d'
PREPARED_COMMENTS_CACHE_KEY = 'search_index_prepared_comments.%d'
PREPARED_INTEGRATION_CACHE_KEY = 'search_index_prepared_integration.%d'

def _average(values):
    length = len(values)
    if length > 0:
        return sum(values) / float(length)
    return 0


def _astrobin_index(values):
    import math
    return _average(values) * math.log(len(values) + 1, 10)


def _prepare_integration(obj):
    deep_sky_acquisitions = DeepSky_Acquisition.objects.filter(image=obj)
    solar_system_acquisition = None
    integration = 0

    try:
        solar_system_acquisition = SolarSystem_Acquisition.objects.get(image=obj)
    except SolarSystem_Acquisition.DoesNotExist:
        pass

    if deep_sky_acquisitions:
        for a in deep_sky_acquisitions:
            if a.duration and a.number:
                integration += (a.duration * a.number)
    elif solar_system_acquisition:
        integration = 0

    cache.set(PREPARED_INTEGRATION_CACHE_KEY % obj.pk, integration, PREPARED_FIELD_CACHE_EXPIRATION)
    return integration


def _prepare_comment_contribution_index(comments):
    min_comment_length = 150
    min_likes = 3

    all_comments = comments \
        .annotate(length=Length('text')) \
        .filter(deleted=False, length__gte=min_comment_length)

    all_comments_with_enough_likes = [x for x in all_comments if len(x.likes) >= min_likes]
    all_comments_count = len(all_comments_with_enough_likes)

    if all_comments_count == 0:
        return 0

    all_likes = 0
    for comment in all_comments_with_enough_likes:
        all_likes += len(comment.likes)

    average = all_likes / float(all_comments_count)
    normalized = []

    for comment in all_comments_with_enough_likes:
        likes = len(comment.likes)
        if likes >= average:
            normalized.append(likes)

    if len(normalized) == 0:
        return 0

    return _astrobin_index(normalized)


def _prepare_forum_post_contribution_index(posts):
    min_post_length = 150
    min_likes = 3

    all_posts = posts \
        .annotate(length=Length('body')) \
        .filter(length__gte=min_post_length)

    all_posts_with_enough_likes = [
        x \
        for x in all_posts \
        if ToggleProperty.objects.toggleproperties_for_object('like', x).count() >= min_likes
    ]
    all_posts_count = len(all_posts_with_enough_likes)

    if all_posts_count == 0:
        return 0

    all_likes = 0
    for post in all_posts_with_enough_likes:
        all_likes += ToggleProperty.objects.toggleproperties_for_object('like', post).count()

    average = all_likes / float(all_posts_count)
    normalized = []

    for post in all_posts_with_enough_likes:
        likes = ToggleProperty.objects.toggleproperties_for_object('like', post).count()
        if likes >= average:
            normalized.append(likes)

    if len(normalized) == 0:
        return 0

    return _astrobin_index(normalized)


def _prepare_likes(obj):
    result = ToggleProperty.objects.toggleproperties_for_object("like", obj).count()
    cache.set(PREPARED_LIKES_CACHE_KEY % obj.pk, result, PREPARED_FIELD_CACHE_EXPIRATION)
    return result

def _prepare_bookmarks(obj):
    result = ToggleProperty.objects.toggleproperties_for_object("bookmark", obj).count()
    cache.set(PREPARED_BOOKMARKS_CACHE_KEY % obj.pk, result, PREPARED_FIELD_CACHE_EXPIRATION)
    return result


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

    result = sum(moon_illuminated_list) / float(len(moon_illuminated_list))
    cache.set(PREPARED_MOON_PHASE_CACHE_KEY % obj.pk, result, PREPARED_FIELD_CACHE_EXPIRATION)
    return result


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
    try:
        result = HitCount.objects.get(object_pk=obj.pk, content_type__name=content_type).hits
    except Exception as e:
        result = 0

    cache.set(PREPARED_VIEWS_CACHE_KEY % obj.pk, result, PREPARED_FIELD_CACHE_EXPIRATION)
    return result


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
    result = NestedComment.objects.filter(
        content_type=ct,
        object_id=obj.id,
        deleted=False).count()
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

    # Average likes of all user's images.
    average_likes = FloatField()

    # Normalized likes (Image Index)
    normalized_likes = FloatField()

    # Total likes received on comments.
    comment_likes_received = IntegerField()

    # Total likes received on forum posts.
    forum_post_likes_received = IntegerField()

    # Total number of likes on all "likeable" elements that can be associated to a user.
    total_likes_received = IntegerField()

    # User reputation based on text content
    # DEPRECATED: remove once contribution_index is populated
    reputation = FloatField()

    # Index based on text content
    contribution_index = FloatField()

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
        return self.get_model().objects.all()

    def get_model(self):
        return User

    def get_updated_field(self):
        return "userprofile__updated"

    def prepare_images(self, obj):
        return Image.objects.filter(user=obj).count()

    def prepare_avg_integration(self, obj):
        integration = 0
        images = 0
        for i in Image.objects.filter(user=obj):
            cached = cache.get(PREPARED_INTEGRATION_CACHE_KEY % i.pk)
            image_integration = cached if cached is not None else _prepare_integration(i)
            if image_integration:
                images += 1
                integration += image_integration

        return (integration / 3600.0) / images if images else 0

    def prepare_likes(self, obj):
        likes = 0
        for i in Image.objects.filter(user=obj):
            cached = cache.get(PREPARED_LIKES_CACHE_KEY % i.pk)
            likes += cached if cached is not None else _prepare_likes(i)
        return likes

    def prepare_likes_given(self, obj):
        return ToggleProperty.objects.toggleproperties_for_model('like', Image, obj).count()
    
    def prepare_average_likes(self, obj):
        likes = self.prepared_data.get('likes')
        if likes is None:
            likes = self.prepare_likes(obj)

        images = self.prepared_data.get('images')
        if images is None:
            images = self.prepare_images(obj)

        return likes / float(images) if images > 0 else 0

    def prepare_normalized_likes(self, obj):
        average = self.prepared_data.get('average_likes')

        if average is None:
            average = self.prepare_average_likes(obj)

        normalized = []

        for i in Image.objects.filter(user=obj).iterator():
            cached = cache.get(PREPARED_LIKES_CACHE_KEY % i.pk)
            likes = cached if cached is not None else i.likes()
            if likes >= average:
                normalized.append(likes)

        if len(normalized) == 0:
            result = 0
        else:
            result = _astrobin_index(normalized)

        if obj.userprofile.astrobin_index_bonus is not None:
            result += obj.userprofile.astrobin_index_bonus

        return result

    def prepare_comment_likes_received(self, obj):
        comments = NestedComment.objects.filter(author=obj)
        likes = 0
        for comment in comments.iterator():
            likes += ToggleProperty.objects.toggleproperties_for_object('like', comment).count()

        return likes

    def prepare_forum_post_likes_received(self, obj):
        posts = Post.objects.filter(user=obj)
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

    # DEPRECATED: remove once contribution_index is populated
    def prepare_reputation(self, obj):
        comments_contribution_index = _prepare_comment_contribution_index(NestedComment.objects.filter(author=obj))
        forum_post_contribution_index = _prepare_forum_post_contribution_index(Post.objects.filter(user=obj))
        return comments_contribution_index + forum_post_contribution_index

    def prepare_contribution_index(self, obj):
        comments_contribution_index = _prepare_comment_contribution_index(NestedComment.objects.filter(author=obj))
        forum_post_contribution_index = _prepare_forum_post_contribution_index(Post.objects.filter(user=obj))
        return comments_contribution_index + forum_post_contribution_index

    def prepare_followers(self, obj):
        return ToggleProperty.objects.filter(
            property_type="follow",
            content_type=ContentType.objects.get_for_model(User),
            object_id=obj.pk
        ).count()

    def prepare_integration(self, obj):
        integration = 0
        for i in Image.objects.filter(user=obj):
            cached = cache.get(PREPARED_INTEGRATION_CACHE_KEY % i.pk)
            integration += cached if cached is not None else _prepare_integration(i)

        return integration / 3600.0

    def prepare_moon_phase(self, obj):
        l = []
        for i in Image.objects.filter(user=obj):
            cached = cache.get(PREPARED_MOON_PHASE_CACHE_KEY % i.pk)
            l.append(cached if cached is not None else _prepare_moon_phase(i))
        if len(l) == 0:
            return 0
        return reduce(lambda x, y: x + y, l) / len(l)

    def prepare_views(self, obj):
        views = 0
        for i in Image.objects.filter(user=obj):
            cached = cache.get(PREPARED_VIEWS_CACHE_KEY % i.pk)
            views += cached if cached is not None else _prepare_views(i, 'image')
        return views

    def prepare_bookmarks(self, obj):
        bookmarks = 0
        for i in Image.objects.filter(user=obj):
            cached = cache.get(PREPARED_BOOKMARKS_CACHE_KEY % i.pk)
            bookmarks += cached if cached is not None else _prepare_bookmarks(i)
        return bookmarks

    def prepare_comments(self, obj):
        comments = 0
        for i in Image.objects.filter(user=obj):
            cached = cache.get(PREPARED_COMMENTS_CACHE_KEY % i.pk)
            comments += cached if cached is not None else _prepare_comments(i)
        return comments

    def prepare_comments_written(self, obj):
        return NestedComment.objects.filter(author=obj, deleted=False).count()

    def prepare_forum_posts(self, obj):
        return Post.objects.filter(user=obj).count()

    def prepare_top_pick_nominations(self, obj):
        return IotdService().get_top_pick_nominations().filter(user=obj).count()

    def prepare_top_picks(self, obj):
        return IotdService().get_top_picks().filter(user=obj).count()

    def prepare_iotds(self, obj):
        return IotdService().get_iotds().filter(image__user=obj).count()

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
    coord_ra_min = FloatField()
    coord_ra_max = FloatField()
    coord_dec_min = FloatField()
    coord_dec_max = FloatField()
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

    solar_system_main_subject_char = CharField(model_attr='solar_system_main_subject', null=True)

    is_deep_sky = BooleanField()
    is_solar_system = BooleanField()
    is_sun = BooleanField()
    is_moon = BooleanField()
    is_planets = BooleanField()
    is_comets = BooleanField()

    is_iotd = BooleanField()
    is_top_pick = BooleanField()
    is_top_pick_nomination = BooleanField()

    license = IntegerField(model_attr='license')

    min_aperture = IntegerField()
    max_aperture = IntegerField()

    min_pixel_size = IntegerField()
    max_pixel_size = IntegerField()

    bookmarks = IntegerField()

    telescope_types = MultiValueField()
    camera_types = MultiValueField()

    comments = IntegerField()

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
        return ["%s, %s" % (x.get("make"), x.get("name")) for x in obj.imaging_telescopes.all().values('make', 'name')]

    def prepare_guiding_telescopes(self, obj):
        return ["%s, %s" % (x.get("make"), x.get("name")) for x in obj.guiding_telescopes.all().values('make', 'name')]

    def prepare_mounts(self, obj):
        return ["%s, %s" % (x.get("make"), x.get("name")) for x in obj.mounts.all().values('make', 'name')]

    def prepare_imaging_cameras(self, obj):
        return ["%s, %s" % (x.get("make"), x.get("name")) for x in obj.imaging_cameras.all().values('make', 'name')]

    def prepare_guiding_cameras(self, obj):
        return ["%s, %s" % (x.get("make"), x.get("name")) for x in obj.guiding_cameras.all().values('make', 'name')]

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

    def prepare_likes(self, obj):
        return _prepare_likes(obj)

    def prepare_integration(self, obj):
        return _prepare_integration(obj)

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

    def prepare_is_iotd(self, obj):
        return hasattr(obj, 'iotd')

    def prepare_is_top_pick(self, obj):
        return obj.iotdvote_set.count() > 0 and not hasattr(obj, 'iotd')

    def prepare_is_top_pick_nomination(self, obj):
        return obj.iotdsubmission_set.count() > 0 and obj.iotdvote_set.count() == 0

    def prepare_objects_in_field(self, obj):
        return obj.solution.objects_in_field if obj.solution else None

    def prepare_countries(self, obj):
        return ' '.join([x.country for x in obj.locations.all() if x.country])


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
