# Python
import unicodedata

# Django
from django.contrib.auth.models import User
from django import forms

# Third party apps
from haystack.query import SearchQuerySet
from haystack.forms import SearchForm
from haystack.generic_views import SearchView
from pybb.models import Post, Topic

from nested_comments.models import NestedComment

from models import Image


FIELDS = (
    # Filtering
    'q',
    'd',
    't',
    'animated',
    'award',
    'camera_type',
    'country',
    'acquisition_type',
    'data_source',
    'field_radius_min',
    'field_radius_max',
    'minimum_data',
    'moon_phase_min',
    'moon_phase_max',
    'license',
    'pixel_scale_min',
    'pixel_scale_max',
    'remote_source',
    'subject_type',
    'telescope_type',

    # Sorting
    'sort'
)


class AstroBinSearchForm(SearchForm):
    # q is inherited from the parent form.

    d = forms.CharField(required=False)
    t = forms.CharField(required=False)
    
    animated = forms.BooleanField(required=False)
    award = forms.CharField(required=False)
    camera_type = forms.CharField(required=False)
    country = forms.CharField(required=False)
    acquisition_type = forms.CharField(required=False)
    data_source = forms.CharField(required=False)
    field_radius_min = forms.IntegerField(required=False)
    field_radius_max = forms.IntegerField(required=False)
    minimum_data = forms.CharField(required=False)
    moon_phase_min = forms.IntegerField(required=False)
    moon_phase_max = forms.IntegerField(required=False)
    license = forms.CharField(required=False)
    pixel_scale_min = forms.FloatField(required=False)
    pixel_scale_max = forms.FloatField(required=False)
    remote_source = forms.CharField(required=False)
    subject_type = forms.CharField(required=False)
    telescope_type = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super(AstroBinSearchForm, self).__init__(args, kwargs)
        self.data = {x: kwargs.pop(x, None) for x in FIELDS}

    def filterByDomain(self, results):
        d = self.cleaned_data.get("d")

        if d is None or d == "":
            d = "i"

        if d == "i":
            results = results.models(Image)
        elif d == "u":
            results = results.models(User)
        elif d == "cf":
            results = results.models(NestedComment, Post, Topic)

        return results

    def filterByType(self, results):
        t = self.cleaned_data.get("t")

        if t is None or t == "":
            t = "all"

        if t != "all":
            results = results.filter(**{t: self.cleaned_data.get('q')})

        return results

    def filterByAnimated(self, results):
        t = self.cleaned_data.get("animated")

        if t:
            results = results.filter(animated=True)

        return results

    def filterByAward(self, results):
        award = self.cleaned_data.get("award")

        if award is not None and award != "":
            types = award.split(',')

            if "iotd" in types:
                results = results.filter(is_iotd=True)

            if "top-pick" in types:
                results = results.filter(is_top_pick=True)

        return results

    def filterByCameraType(self, results):
        camera_type = self.cleaned_data.get("camera_type")

        if camera_type is not None and camera_type != "":
            types = camera_type.split(',')
            results = results.filter(camera_types__in=types)

        return results

    def filterByCountry(self, results):
        country = self.cleaned_data.get("country")

        if country is not None and country != "":
            results = results.filter(countries=country)

        return results

    def filterByAcquisitionType(self, results):
        acquisition_type = self.cleaned_data.get("acquisition_type")

        if acquisition_type is not None and acquisition_type != "":
            results = results.filter(acquisition_type=acquisition_type)

        return results

    def filterByDataSource(self, results):
        data_source = self.cleaned_data.get("data_source")

        if data_source is not None and data_source != "":
            results = results.filter(data_source=data_source)

        return results

    def filterByFieldRadius(self, results):
        try:
            min = float(self.cleaned_data.get("field_radius_min"))
            results = results.filter(field_radius__gte=min)
        except TypeError:
            pass

        try:
            max = float(self.cleaned_data.get("field_radius_max"))
            results = results.filter(field_radius__lte=max)
        except TypeError:
            pass

        return results

    def filterByMinimumData(self, results):
        minimum_data = self.cleaned_data.get("minimum_data")

        if minimum_data is not None and minimum_data != "":
            minimum = minimum_data.split(',')

            for data in minimum:
                if data == 't':
                    results = results.exclude(_missing_="imaging_telescopes")
                if data == "c":
                    results = results.exclude(_missing_="imaging_cameras")
                if data == "a":
                    results = results.exclude(_missing_="first_acquisition_date")
                if data == "s":
                    results = results.exclude(_missing_="pixel_scale")

        return results

    def filterByMoonPhase(self, results):
        try:
            min = float(self.cleaned_data.get("moon_phase_min"))
            results = results.filter(moon_phase__gte=min)
        except TypeError:
            pass

        try:
            max = float(self.cleaned_data.get("moon_phase_max"))
            results = results.filter(moon_phase__lte=max)
        except TypeError:
            pass

        return results

    def filterByLicense(self, results):
        license = self.cleaned_data.get("license")

        if license is not None and license != "":
            licenses = license.split(',')
            results = results.filter(license__in=licenses)

        return results

    def filterByPixelScale(self, results):
        try:
            min = float(self.cleaned_data.get("pixel_scale_min"))
            results = results.filter(pixel_scale__gte=min)
        except TypeError:
            pass

        try:
            max = float(self.cleaned_data.get("pixel_scale_max"))
            results = results.filter(pixel_scale__lte=max)
        except TypeError:
            pass

        return results

    def filterByRemoteSource(self, results):
        remote_source = self.cleaned_data.get("remote_source")

        if remote_source is not None and remote_source != "":
            results = results.filter(remote_source=remote_source)

        return results

    def filterBySubjectType(self, results):
        subject_type = self.cleaned_data.get("subject_type")

        if subject_type == "deep_sky":
            results = results.filter(subject_type=100)
        elif subject_type == "solar_system":
            results = results.filter(subject_type=200)
        elif subject_type == "wide":
            results = results.filter(subject_type=300)
        elif subject_type == "trails":
            results = results.filter(subject_type=400)
        elif subject_type == "aurora":
            results = results.filter(subject_type=450)
        elif subject_type == "gear":
            results = results.filter(subject_type=500)
        elif subject_type == "other":
            results = results.filter(subject_type=600)
        elif subject_type == "sun":
            results = results.filter(solar_system_main_subject=0)
        elif subject_type == "moon":
            results = results.filter(solar_system_main_subject=1)
        elif subject_type == "mercury":
            results = results.filter(solar_system_main_subject=2)
        elif subject_type == "venus":
            results = results.filter(solar_system_main_subject=3)
        elif subject_type == "mars":
            results = results.filter(solar_system_main_subject=4)
        elif subject_type == "jupiter":
            results = results.filter(solar_system_main_subject=5)
        elif subject_type == "saturn":
            results = results.filter(solar_system_main_subject=6)
        elif subject_type == "uranus":
            results = results.filter(solar_system_main_subject=7)
        elif subject_type == "neptune":
            results = results.filter(solar_system_main_subject=8)
        elif subject_type == "minor_planet":
            results = results.filter(solar_system_main_subject=9)
        elif subject_type == "comet":
            results = results.filter(solar_system_main_subject=10)
        elif subject_type == "other_solar_system":
            results = results.filter(solar_system_main_subject=11)

        return results

    def filterByTelescopeType(self, results):
        telescope_type = self.cleaned_data.get("telescope_type")

        if telescope_type is not None and telescope_type != "":
            types = telescope_type.split(',')
            results = results.filter(telescope_types__in=types)

        return results

    def sort(self, results):
        order_by = None
        domain = self.cleaned_data.get('d', 'i')

        # Default to upload order for images.
        if domain == 'i':
            order_by = ('-published', '-uploaded')

        # Default to updated/created order for comments/forums.
        if domain == 'cf':
            order_by = ('-updated', '-created')

        # Prefer user's choice of course.
        if self.data.get('sort') is not None:
            order_by = self.data.get('sort')

            # Special fixes for some fields.
            if order_by.endswith('field_radius'):
                results = results.exclude(_missing_='field_radius')
            elif order_by.endswith('pixel_scale'):
                results = results.exclude(_missing_='pixel_scale')

        if order_by is not None:
            if type(order_by) is list or type(order_by) is tuple:
                results = results.order_by(*order_by)
            else:
                results = results.order_by(order_by)

        return results

    def search(self):
        q = self.cleaned_data.get('q')

        try:
            q = unicodedata.normalize('NFKD', q).encode('ascii', 'ignore')
        except:
            pass

        if q is None or q == u"":
            sqs = SearchQuerySet().all()
        else:
            sqs = self.searchqueryset.auto_query(q)

        sqs = self.filterByDomain(sqs)

        # Images
        sqs = self.filterByType(sqs)
        sqs = self.filterByAnimated(sqs)
        sqs = self.filterByAward(sqs)
        sqs = self.filterByCameraType(sqs)
        sqs = self.filterByCountry(sqs)
        sqs = self.filterByAcquisitionType(sqs)
        sqs = self.filterByDataSource(sqs)
        sqs = self.filterByLicense(sqs)
        sqs = self.filterByFieldRadius(sqs)
        sqs = self.filterByMinimumData(sqs)
        sqs = self.filterByMoonPhase(sqs)
        sqs = self.filterByPixelScale(sqs)
        sqs = self.filterByRemoteSource(sqs)
        sqs = self.filterBySubjectType(sqs)
        sqs = self.filterByTelescopeType(sqs)

        sqs = self.sort(sqs)

        return sqs


class AstroBinSearchView(SearchView):
    query = None
    results = None
    form_class = AstroBinSearchForm

    def get_form(self, form_class=None):
        return self.get_form_class()(**{x: self.request.GET.get(x, None) for x in FIELDS})

    def get_context_data(self, **kwargs):
        context = super(AstroBinSearchView, self).get_context_data(**kwargs)
        context['object_list'] = self.queryset
        return context
