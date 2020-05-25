from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from persistent_messages.models import Message
from tastypie import fields, http
from tastypie.authentication import Authentication
from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS

from astrobin.models import Location, Image, ImageRevision, ImageOfTheDay, App, Collection, UserProfile
from astrobin.views import get_image_or_404
from astrobin_apps_images.services import ImageService
from astrobin_apps_iotd.models import IotdVote
from astrobin_apps_premium.utils import premium_get_valid_usersubscription
from toggleproperties.models import ToggleProperty


class AppAuthentication(Authentication):
    def is_authenticated(self, request, **kwargs):
        try:
            app_key = request.GET.get('api_key')
            app_secret = request.GET.get('api_secret')
        except:
            return False

        if app_key == '' or app_secret == '':
            return False

        try:
            app = App.objects.get(secret=app_secret, key=app_key)
        except App.DoesNotExist:
            return False

        return True


class LocationResource(ModelResource):
    """
    name = fields.CharField()
    city = fields.CharField()
    state = fields.CharField()
    country = fields.CharField()
    altitude = fields.IntegerField()
    """

    class Meta:
        authentication = AppAuthentication()
        queryset = Location.objects.all()
        fields = [
            'name',
            'city',
            'state',
            'country',
            'altitude',
        ]
        allowed_methods = ['get']


class ImageRevisionResource(ModelResource):
    image = fields.ForeignKey('astrobin.api.ImageResource', 'image')
    url_thumb = fields.CharField()
    url_gallery = fields.CharField()
    url_regular = fields.CharField()
    url_regular_sharpened = fields.CharField()
    url_hd = fields.CharField()
    url_hd_sharpened = fields.CharField()
    url_real = fields.CharField()
    url_duckduckgo = fields.CharField()
    url_duckduckgo_small = fields.CharField()

    is_solved = fields.BooleanField()

    ra = fields.DecimalField()
    dec = fields.DecimalField()
    pixscale = fields.DecimalField()
    orientation = fields.DecimalField()
    radius = fields.DecimalField()

    class Meta:
        authentication = AppAuthentication()
        queryset = ImageRevision.objects.filter(image__is_wip=False, corrupted=False)
        fields = [
            'uploaded',
            'w',
            'h',

            'url_thumb',
            'url_gallery',
            'url_regular',
            'url_regular_sharpened',
            'url_hd',
            'url_hd_sharpened',
            'url_real',
            'url_duckduckgo',
            'url_duckduckgo_small',

            'is_final',
            'is_solved',

            'ra',
            'dec',
            'pixscale',
            'orientation',
            'radius',
        ]

        allowed_methods = ['get']

    def dehydrate_url_thumb(self, bundle):
        return '%s/%s/%s/rawthumb/thumb/' % (settings.BASE_URL, bundle.obj.image.get_id(), bundle.obj.label)

    def dehydrate_url_gallery(self, bundle):
        return '%s/%s/%s/rawthumb/gallery/' % (settings.BASE_URL, bundle.obj.image.get_id(), bundle.obj.label)

    def dehydrate_url_regular(self, bundle):
        return '%s/%s/%s/rawthumb/regular/' % (settings.BASE_URL, bundle.obj.image.get_id(), bundle.obj.label)

    def dehydrate_url_regular_sharpened(self, bundle):
        return '%s/%s/%s/rawthumb/regular_sharpened/' % (settings.BASE_URL, bundle.obj.image.get_id(), bundle.obj.label)

    def dehydrate_url_hd(self, bundle):
        return '%s/%s/%s/rawthumb/hd/' % (settings.BASE_URL, bundle.obj.image.get_id(), bundle.obj.label)

    def dehydrate_url_hd_sharpened(self, bundle):
        return '%s/%s/%s/rawthumb/hd_sharpened/' % (settings.BASE_URL, bundle.obj.image.get_id(), bundle.obj.label)

    def dehydrate_url_real(self, bundle):
        return '%s/%s/%s/rawthumb/real/' % (settings.BASE_URL, bundle.obj.image.get_id(), bundle.obj.label)

    def dehydrate_url_duckduckgo(self, bundle):
        return '%s/%s/%s/rawthumb/duckduckgo/' % (settings.BASE_URL, bundle.obj.image.get_id(), bundle.obj.label)

    def dehydrate_url_duckduckgo_small(self, bundle):
        return '%s/%s/%s/rawthumb/duckduckgo_small/' % (settings.BASE_URL, bundle.obj.image.get_id(), bundle.obj.label)

    def dehydrate_is_solved(self, bundle):
        return bundle.obj.solution != None

    def dehydrate_ra(self, bundle):
        if bundle.obj.solution:
            return bundle.obj.solution.ra
        return None

    def dehydrate_dec(self, bundle):
        if bundle.obj.solution:
            return bundle.obj.solution.dec
        return None

    def dehydrate_pixscale(self, bundle):
        if bundle.obj.solution:
            return bundle.obj.solution.pixscale
        return None

    def dehydrate_orientation(self, bundle):
        if bundle.obj.solution:
            return bundle.obj.solution.orientation
        return None

    def dehydrate_radius(self, bundle):
        if bundle.obj.solution:
            return bundle.obj.solution.radius
        return None


class ImageResource(ModelResource):
    user = fields.CharField('user__username')
    revisions = fields.ToManyField(ImageRevisionResource, 'revisions')

    subjects = fields.ListField()

    imaging_telescopes = fields.ListField()
    imaging_cameras = fields.ListField()

    uploaded = fields.DateField('uploaded')
    published = fields.DateField('published')
    updated = fields.DateField('updated')

    locations = fields.ToManyField(LocationResource, 'locations')

    url_thumb = fields.CharField()
    url_gallery = fields.CharField()
    url_regular = fields.CharField()
    url_hd = fields.CharField()
    url_real = fields.CharField()
    url_duckduckgo = fields.CharField()
    url_duckduckgo_small = fields.CharField()

    is_solved = fields.BooleanField()

    ra = fields.DecimalField()
    dec = fields.DecimalField()
    pixscale = fields.DecimalField()
    orientation = fields.DecimalField()
    radius = fields.DecimalField()

    class Meta:
        authentication = AppAuthentication()
        queryset = Image.objects.filter(corrupted=False, is_wip=False)
        fields = [
            'id',
            'hash',
            'title',
            'w',
            'h',
            'locations',

            'url_thumb',
            'url_gallery',
            'url_regular',
            'url_hd',
            'url_real',
            'url_duckduckgo',
            'url_duckduckgo_small',

            'uploaded',
            'published',
            'description',
            'h',
            'w',
            'animated',
            'link',
            'link_to_fits',
            'license',
            # TODO: likes

            'is_final',
            'is_solved',

            'ra',
            'dec',
            'pixscale',
            'orientation',
            'radius',
        ]
        allowed_methods = ['get']

        filtering = {
            'title': ALL,
            'description': ALL,
            'is_solved': ALL,
            'user': ALL_WITH_RELATIONS,
            'uploaded': ALL,
            'published': ALL,
            'imaging_telescopes': ALL,
            'imaging_cameras': ALL,
            'w': ALL,
            'h': ALL,
        }
        ordering = ['uploaded']

    def dehydrate_url_thumb(self, bundle):
        return '%s/%s/0/rawthumb/thumb/' % (settings.BASE_URL, bundle.obj.get_id())

    def dehydrate_url_gallery(self, bundle):
        return '%s/%s/0/rawthumb/gallery/' % (settings.BASE_URL, bundle.obj.get_id())

    def dehydrate_url_regular(self, bundle):
        return '%s/%s/0/rawthumb/regular/' % (settings.BASE_URL, bundle.obj.get_id())

    def dehydrate_url_hd(self, bundle):
        return '%s/%s/0/rawthumb/hd/' % (settings.BASE_URL, bundle.obj.get_id())

    def dehydrate_url_real(self, bundle):
        return '%s/%s/0/rawthumb/real/' % (settings.BASE_URL, bundle.obj.get_id())

    def dehydrate_url_duckduckgo(self, bundle):
        return '%s/%s/0/rawthumb/duckduckgo/' % (settings.BASE_URL, bundle.obj.get_id())

    def dehydrate_url_duckduckgo_small(self, bundle):
        return '%s/%s/0/rawthumb/duckduckgo_small/' % (settings.BASE_URL, bundle.obj.get_id())

    def dehydrate_is_solved(self, bundle):
        return bundle.obj.solution != None

    def dehydrate_subjects(self, bundle):
        if bundle.obj.solution:
            subjects = bundle.obj.solution.objects_in_field
            if subjects:
                subjects = subjects.split(',')
            else:
                subjects = []

            solar_system_main_subject = bundle.obj.solar_system_main_subject

            ret = subjects

            if solar_system_main_subject:
                ret.append(ImageService(bundle.obj).get_solar_system_main_subject_label())

            return ret
        return []

    def dehydrate_ra(self, bundle):
        if bundle.obj.solution:
            return bundle.obj.solution.ra
        return None

    def dehydrate_dec(self, bundle):
        if bundle.obj.solution:
            return bundle.obj.solution.dec
        return None

    def dehydrate_pixscale(self, bundle):
        if bundle.obj.solution:
            return bundle.obj.solution.pixscale
        return None

    def dehydrate_orientation(self, bundle):
        if bundle.obj.solution:
            return bundle.obj.solution.orientation
        return None

    def dehydrate_radius(self, bundle):
        if bundle.obj.solution:
            return bundle.obj.solution.radius
        return None

    def dehydrate_imaging_telescopes(self, bundle):
        telescopes = bundle.obj.imaging_telescopes.all()
        return [unicode(x) for x in telescopes]

    def dehydrate_imaging_cameras(self, bundle):
        cameras = bundle.obj.imaging_cameras.all()
        return [unicode(x) for x in cameras]

    def get_detail(self, request, **kwargs):
        """
        Returns a single serialized resource.

        Calls ``cached_obj_get/obj_get`` to provide the data, then handles that result
        set and serializes it.

        Should return a HttpResponse (200 OK).
        """

        try:
            obj = get_image_or_404(self._meta.queryset, kwargs.get("pk"))
        except Http404:
            return http.HttpNotFound()

        bundle = self.build_bundle(obj=obj, request=request)
        bundle = self.full_dehydrate(bundle)
        bundle = self.alter_detail_data_to_serialize(request, bundle)
        return self.create_response(request, bundle)

    def build_filters(self, filters=None, ignore_bad_filters=False):
        subjects = None
        ids = None
        user = None

        if filters is None:
            filters = {}

        if 'subjects' in filters:
            subjects = filters['subjects']
            del filters['subjects']

        if 'ids' in filters:
            ids = filters['ids']
            del filters['ids']

        if 'user' in filters:
            user = filters['user']
            del filters['user']

        orm_filters = super(ImageResource, self).build_filters(filters, ignore_bad_filters)

        if subjects:
            from astrobin_apps_platesolving.models import Solution

            def fix_catalog(name):
                capitalize = ('ngc', 'm', 'b', 'ic', 'ugc', 'pgc',)
                if name.lower() in [x.lower() for x in capitalize]:
                    return name.upper() + ' '
                remove = ('name',)
                if name.lower() in [x.lower() for x in remove]:
                    return ''
                return name + ' '

            def fix_name(name):
                import re
                fix = re.compile('^(?P<catalog>M|NGC)(?P<name>\d+)', re.IGNORECASE)
                m = fix.match(name)
                if m:
                    return '%s%s' % (fix_catalog(m.group('catalog')), m.group('name'))
                return name

            r = r"\y{0}\y".format(fix_name(subjects))
            qs = Solution.objects.filter(objects_in_field__iregex=r)
            orm_filters['pk__in'] = [i.object_id for i in qs]

        if ids:
            orm_filters['pk__in'] = ids.split(',')

        if user:
            orm_filters['user__username'] = user

        return orm_filters


class ImageOfTheDayResource(ModelResource):
    image = fields.ForeignKey('astrobin.api.ImageResource', 'image')
    runnerup_1 = fields.ForeignKey('astrobin.api.ImageResource', 'runnerup_1', null=True)
    runnerup_2 = fields.ForeignKey('astrobin.api.ImageResource', 'runnerup_2', null=True)

    class Meta:
        authentication = AppAuthentication()
        queryset = ImageOfTheDay.objects.filter(image__corrupted=False)
        fields = [
            'image',
            'runnerup_1',
            'runnerup_2',
            'date',
        ]
        allowed_methods = ['get']

    def dehydrate_image(self, bundle):
        return "/api/v1/image/%s" % bundle.obj.image.get_id()


class TopPickResource(ModelResource):
    image = fields.ForeignKey('astrobin.api.ImageResource', 'image')
    date = fields.DateField('date')

    class Meta:
        authentication = AppAuthentication()
        queryset = IotdVote.objects.filter(image__corrupted=False)
        fields = [
            'image',
            'date'
        ]
        allowed_methods = ['get']

    def dehydrate_image(self, bundle):
        return "/api/v1/image/%s" % bundle.obj.image.get_id()


class CollectionResource(ModelResource):
    date_created = fields.DateField('date_created')
    date_updated = fields.DateField('date_updated')
    user = fields.CharField('user__username')
    name = fields.CharField('name')
    description = fields.CharField('description')
    images = fields.ToManyField(ImageResource, 'images')

    class Meta:
        authentication = AppAuthentication()
        allowed_methods = ['get']
        queryset = Collection.objects.all()
        filtering = {
            'name': ALL,
            'description': ALL,
            'user': ALL_WITH_RELATIONS,
        }
        ordering = ['-date_created']

    def dehydrate_images(self, bundle):
        images = bundle.obj.images.all()
        return ["/api/v1/image/%s" % image.get_id() for image in images]


class UserProfileResource(ModelResource):
    username = fields.CharField("user__username")
    last_login = fields.DateTimeField("user__last_login", null=True)
    date_joined = fields.DateTimeField("user__date_joined")

    image_count = fields.IntegerField()
    received_likes_count = fields.IntegerField()
    followers_count = fields.IntegerField()
    following_count = fields.IntegerField()
    total_notifications_count = fields.IntegerField()
    unread_notifications_count = fields.IntegerField()
    premium_subscription = fields.CharField()
    premium_subscription_expiration = fields.DateField()

    class Meta:
        authentication = AppAuthentication()
        allowed_methods = ["get"]
        queryset = UserProfile.objects.all()
        filtering = {
            "username": ALL
        }
        excludes = (
            'accept_tos',
            'autosubscribe',
            'company_description',
            'company_name',
            'company_website',
            'default_frontpage_section',
            'default_gallery_sorting',
            'default_license',
            'default_watermark',
            'default_watermark_opacity',
            'default_watermark_position',
            'default_watermark_size',
            'default_watermark_text',
            'deleted',
            'exclude_from_competitions',
            'inactive_account_reminder_sent',
            'premium_counter',
            'premium_offer',
            'premium_offer_expiration',
            'premium_offer_sent',
            'receive_forum_emails',
            'receive_important_communications',
            'receive_marketing_and_commercial_material',
            'receive_newsletter',
            'retailer_country',
            'seen_email_permissions',
            'seen_realname',
            'show_signatures',
            'signature',
            'signature_html',
        )
        ordering = ['-date_joined']

    def dehydrate_image_count(self, bundle):
        return Image.objects.filter(user=bundle.obj.user, corrupted=False, is_wip=False).count()

    def dehydrate_received_likes_count(self, bundle):
        likes = 0
        for i in Image.objects.filter(user=bundle.obj.user):
            likes += ToggleProperty.objects.toggleproperties_for_object("like", i).count()
        return likes

    def dehydrate_followers_count(self, bundle):
        return ToggleProperty.objects.filter(
            property_type="follow",
            content_type=ContentType.objects.get_for_model(User),
            object_id=bundle.obj.user.pk,
        ).count()

    def dehydrate_following_count(self, bundle):
        return ToggleProperty.objects.filter(
            property_type="follow",
            user=bundle.obj.user,
        ).count()

    def dehydrate_total_notifications_count(self, bundle):
        return Message.objects.filter(user=bundle.obj.user).count()

    def dehydrate_unread_notifications_count(self, bundle):
        return Message.objects.filter(user=bundle.obj.user, read=False).count()

    def dehydrate_premium_subscription(self, bundle):
        user_subscription = premium_get_valid_usersubscription(bundle.obj.user)
        return user_subscription.subscription.name if user_subscription else None

    def dehydrate_premium_subscription_expiration(self, bundle):
        user_subscription = premium_get_valid_usersubscription(bundle.obj.user)
        return user_subscription.expires if user_subscription else None
