from django.conf import settings
from django.db.models import Q

from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie import fields
from tastypie.authentication import Authentication

from astrobin.models import Image, ImageRevision, ImageOfTheDay, App
from astrobin.models import SOLAR_SYSTEM_SUBJECT_CHOICES


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
            app = App.objects.get(secret = app_secret, key = app_key)
        except App.DoesNotExist:
            return False

        return True


class ImageRevisionResource(ModelResource):
    image = fields.ForeignKey('astrobin.api.ImageResource', 'image')
    url_thumb = fields.CharField()
    url_gallery = fields.CharField()
    url_regular = fields.CharField()
    url_hd = fields.CharField()
    url_real = fields.CharField()
    url_duckduckgo = fields.CharField()
    url_duckduckgo_small = fields.CharField()

    is_solved = fields.BooleanField()

    class Meta:
        authentication = AppAuthentication()
        queryset = ImageRevision.objects.filter(image__is_wip = False)
        fields = [
            'uploaded',
            'w',
            'h',

            'url_thumb',
            'url_gallery',
            'url_regular',
            'url_hd',
            'url_real',
            'url_duckduckgo',
            'url_duckduckgo_small',

            'is_final',
            'is_solved',
        ]

        allowed_methods = ['get']

    def dehydrate_url_thumb(self, bundle):
        return '%s/%d/%s/rawthumb/thumb/' % (settings.ASTROBIN_BASE_URL, bundle.obj.image.id, bundle.obj.label)

    def dehydrate_url_gallery(self, bundle):
        return '%s/%d/%s/rawthumb/gallery/' % (settings.ASTROBIN_BASE_URL, bundle.obj.image.id, bundle.obj.label)

    def dehydrate_url_regular(self, bundle):
        return '%s/%d/%s/rawthumb/regular/' % (settings.ASTROBIN_BASE_URL, bundle.obj.image.id, bundle.obj.label)

    def dehydrate_url_hd(self, bundle):
        return '%s/%d/%s/rawthumb/hd/' % (settings.ASTROBIN_BASE_URL, bundle.obj.image.id, bundle.obj.label)

    def dehydrate_url_real(self, bundle):
        return '%s/%d/%s/rawthumb/real/' % (settings.ASTROBIN_BASE_URL, bundle.obj.image.id, bundle.obj.label)

    def dehydrate_url_duckduckgo(self, bundle):
        return '%s/%d/%s/rawthumb/duckduckgo/' % (settings.ASTROBIN_BASE_URL, bundle.obj.image.id, bundle.obj.label)

    def dehydrate_url_duckduckgo_small(self, bundle):
        return '%s/%d/%s/rawthumb/duckduckgo_small/' % (settings.ASTROBIN_BASE_URL, bundle.obj.image.id, bundle.obj.label)

    def dehydrate_is_solved(self, bundle):
        return bundle.obj.solution != None


class ImageResource(ModelResource):
    user = fields.CharField('user__username')
    revisions = fields.ToManyField(ImageRevisionResource, 'revisions')

    subjects = fields.ListField()

    imaging_telescopes = fields.ListField()
    imaging_cameras = fields.ListField()

    uploaded = fields.DateField('uploaded')
    updated = fields.DateField('updated')

    url_thumb = fields.CharField()
    url_gallery = fields.CharField()
    url_regular = fields.CharField()
    url_hd = fields.CharField()
    url_real = fields.CharField()
    url_duckduckgo = fields.CharField()
    url_duckduckgo_small = fields.CharField()

    is_solved = fields.BooleanField()

    class Meta:
        authentication = AppAuthentication()
        queryset = Image.objects.all()
        fields = [
            'id',
            'title',

            'url_thumb',
            'url_gallery',
            'url_regular',
            'url_hd',
            'url_real',
            'url_duckduckgo',
            'url_duckduckgo_small',

            'uploaded',
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
        ]
        allowed_methods = ['get']

        filtering = {
            'title': ALL,
            'description': ALL,
            'is_solved': ALL,
            'user': ALL_WITH_RELATIONS,
            'uploaded': ALL,
            'imaging_telescopes': ALL,
            'imaging_cameras': ALL,
        }
        ordering = ['uploaded']

    def dehydrate_url_thumb(self, bundle):
        return '%s/%d/0/rawthumb/thumb/' % (settings.ASTROBIN_BASE_URL, bundle.obj.id)

    def dehydrate_url_gallery(self, bundle):
        return '%s/%d/0/rawthumb/gallery/' % (settings.ASTROBIN_BASE_URL, bundle.obj.id)

    def dehydrate_url_regular(self, bundle):
        return '%s/%d/0/rawthumb/regular/' % (settings.ASTROBIN_BASE_URL, bundle.obj.id)

    def dehydrate_url_hd(self, bundle):
        return '%s/%d/0/rawthumb/hd/' % (settings.ASTROBIN_BASE_URL, bundle.obj.id)

    def dehydrate_url_real(self, bundle):
        return '%s/%d/0/rawthumb/real/' % (settings.ASTROBIN_BASE_URL, bundle.obj.id)

    def dehydrate_url_duckduckgo(self, bundle):
        return '%s/%d/0/rawthumb/duckduckgo/' % (settings.ASTROBIN_BASE_URL, bundle.obj.id)

    def dehydrate_url_duckduckgo_small(self, bundle):
        return '%s/%d/0/rawthumb/duckduckgo_small/' % (settings.ASTROBIN_BASE_URL, bundle.obj.id)

    def dehydrate_is_solved(self, bundle):
        return bundle.obj.solution != None

    def dehydrate_subjects(self, bundle):
        if bundle.obj.solution:
            subjects = bundle.obj.solution.objects_in_field
            if subjects:
                subjects = subjects.split(',')
            else:
                subjects = []

            ssms = bundle.obj.solar_system_main_subject

            ret = subjects

            if ssms:
                ret.append(SOLAR_SYSTEM_SUBJECT_CHOICES[ssms][1])

            return ret
        return []

    def dehydrate_imaging_telescopes(self, bundle):
        telescopes = bundle.obj.imaging_telescopes.all()
        return [unicode(x) for x in telescopes]

    def dehydrate_imaging_cameras(self, bundle):
        cameras = bundle.obj.imaging_cameras.all()
        return [unicode(x) for x in cameras]

    def build_filters(self, filters = None):
        subjects = None
        ids = None

        if filters is None:
            filters = {}

        if 'subjects' in filters:
            subjects = filters['subjects']
            del filters['subjects']

        if 'ids' in filters:
            ids = filters['ids']
            del filters['ids']

        orm_filters = super(ImageResource, self).build_filters(filters)

        if subjects:
            from astrobin_apps_platesolving.models import Solution
            qs = Solution.objects.filter(objects_in_field__icontains = subjects)
            orm_filters['pk__in'] = [i.pk for i in qs]

        if ids:
            orm_filters['pk__in'] = ids.split(',')

        return orm_filters


class ImageOfTheDayResource(ModelResource):
    image = fields.ForeignKey('astrobin.api.ImageResource', 'image')
    runnerup_1 = fields.ForeignKey('astrobin.api.ImageResource', 'runnerup_1')
    runnerup_2 = fields.ForeignKey('astrobin.api.ImageResource', 'runnerup_2')

    class Meta:
        authentication = AppAuthentication()
        queryset = ImageOfTheDay.objects.all()
        fields = [
            'image',
            'runnerup_1',
            'runnerup_2',
            'date',
        ]
