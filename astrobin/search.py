import re
import unicodedata
from operator import or_

from django import forms
from django.contrib.auth.models import User
from django.db.models import Q
from haystack.forms import SearchForm
from haystack.generic_views import SearchView
from haystack.inputs import Clean, BaseInput
from haystack.query import SearchQuerySet
from pybb.models import Post, Topic

from astrobin.enums import SolarSystemSubject, SubjectType
from astrobin_apps_equipment.models import EquipmentBrandListing
from nested_comments.models import NestedComment
from .models import Image

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
    'date_published_min',
    'date_published_max',
    'date_acquired_min',
    'date_acquired_max',
    'field_radius_min',
    'field_radius_max',
    'minimum_data',
    'moon_phase_min',
    'moon_phase_max',
    'license',
    'coord_ra_min',
    'coord_ra_max',
    'coord_dec_min',
    'coord_dec_max',
    'pixel_scale_min',
    'pixel_scale_max',
    'remote_source',
    'subject_type',
    'telescope_type',
    'integration_time_min',
    'integration_time_max',
    'constellation',
    'subject',
    'telescope',
    'camera',
    'bortle_scale_min',
    'bortle_scale_max',

    # Sorting
    'sort'
)


class CustomContain(BaseInput):
    """
    An input type for making wildcard matches.
    """
    input_type_name = 'custom_contain'

    def prepare(self, query_obj):
        query_string = super(CustomContain, self).prepare(query_obj)
        query_string = query_obj.clean(query_string)

        exact_bits = [Clean(bit).prepare(query_obj) for bit in query_string.split(' ') if bit]
        query_string = u' '.join(exact_bits)

        return u'*{}*'.format(query_string)


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
    date_published_min = forms.CharField(required=False)
    date_published_max = forms.CharField(required=False)
    date_acquired_min = forms.CharField(required=False)
    date_acquired_max = forms.CharField(required=False)
    field_radius_min = forms.FloatField(required=False)
    field_radius_max = forms.FloatField(required=False)
    minimum_data = forms.CharField(required=False)
    moon_phase_min = forms.FloatField(required=False)
    moon_phase_max = forms.FloatField(required=False)
    license = forms.CharField(required=False)
    coord_ra_min = forms.FloatField(required=False)
    coord_ra_max = forms.FloatField(required=False)
    coord_dec_min = forms.FloatField(required=False)
    coord_dec_max = forms.FloatField(required=False)
    pixel_scale_min = forms.FloatField(required=False)
    pixel_scale_max = forms.FloatField(required=False)
    remote_source = forms.CharField(required=False)
    subject_type = forms.CharField(required=False)
    telescope_type = forms.CharField(required=False)
    integration_time_min = forms.FloatField(required=False)
    integration_time_max = forms.FloatField(required=False)
    constellation = forms.CharField(required=False)
    subject = forms.CharField(required=False)
    telescope = forms.CharField(required=False)
    camera = forms.CharField(required=False)
    bortle_scale_min = forms.FloatField(required=False)
    bortle_scale_max = forms.FloatField(required=False)

    def __init__(self, *args, **kwargs):
        super(AstroBinSearchForm, self).__init__(args, kwargs)
        self.data = {x: kwargs.pop(x, None) for x in FIELDS}

    def filter_by_domain(self, results):
        d = self.cleaned_data.get("d")

        if d is None or d == "":
            d = "i"

        if d == "i":
            results = results.models(Image, EquipmentBrandListing).order_by('-django_ct')
        elif d == "u":
            results = results.models(User)
        elif d == "cf":
            results = results.models(NestedComment, Post, Topic)

        return results

    def filter_by_type(self, results):
        t = self.cleaned_data.get("t")

        if t is None or t == "":
            t = "all"

        if t != "all":
            results = results.filter(**{t: self.cleaned_data.get('q')})

        return results

    def filter_by_animated(self, results):
        t = self.cleaned_data.get("animated")

        if t:
            results = results.filter(animated=True)

        return results

    def filter_by_award(self, results):
        award = self.cleaned_data.get("award")
        queries = []

        if award is not None and award != "":
            types = award.split(',')

            if "iotd" in types:
                queries.append(Q(is_iotd=True))

            if "top-pick" in types:
                queries.append(Q(is_top_pick=True))

            if "top-pick-nomination" in types:
                queries.append(Q(is_top_pick_nomination=True))

        if len(queries) > 0:
            results = results.filter(reduce(or_, queries))

        return results

    def filter_by_camera_type(self, results):
        camera_type = self.cleaned_data.get("camera_type")

        if camera_type is not None and camera_type != "":
            types = camera_type.split(',')
            results = results.filter(camera_types__in=types)

        return results

    def filter_by_country(self, results):
        country = self.cleaned_data.get("country")

        if country is not None and country != "":
            results = results.filter(countries=CustomContain('__%s__' % country))

        return results

    def filter_by_acquisition_type(self, results):
        acquisition_type = self.cleaned_data.get("acquisition_type")

        if acquisition_type is not None and acquisition_type != "":
            results = results.filter(acquisition_type=acquisition_type)

        return results

    def filter_by_data_source(self, results):
        data_source = self.cleaned_data.get("data_source")

        if data_source is not None and data_source != "":
            results = results.filter(data_source=data_source)

        return results

    def filter_by_date_published(self, results):
        date_published_min = self.cleaned_data.get("date_published_min")
        date_published_max = self.cleaned_data.get("date_published_max")

        if date_published_min is not None and date_published_min != "":
            results = results.filter(published__gte=date_published_min)

        if date_published_max is not None and date_published_max != "":
            results = results.filter(published__lte=date_published_max)

        return results

    def filter_by_date_acquired(self, results):
        date_acquired_min = self.cleaned_data.get("date_acquired_min")
        date_acquired_max = self.cleaned_data.get("date_acquired_max")

        if date_acquired_min is not None and date_acquired_min != "":
            results = results.filter(first_acquisition_date__gte=date_acquired_min)

        if date_acquired_max is not None and date_acquired_max != "":
            results = results.filter(last_acquisition_date__lte=date_acquired_max)

        return results

    def filter_by_field_radius(self, results):
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

    def filter_by_minimum_data(self, results):
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

    def filter_by_moon_phase(self, results):
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

    def filter_by_license(self, results):
        license = self.cleaned_data.get("license")

        if license is not None and license != "":
            licenses = license.split(',')
            results = results.filter(license_name__in=licenses)

        return results

    def filter_by_coords(self, results):
        # Intersection between the filter ra,dec area and the image area.
        try:
            ra_min = float(self.cleaned_data.get("coord_ra_min"))
            ra_max = float(self.cleaned_data.get("coord_ra_max"))
            results = results.filter(coord_ra_min__lte=ra_max)
            results = results.filter(coord_ra_max__gte=ra_min)
        except TypeError:
            pass

        try:
            dec_min = float(self.cleaned_data.get("coord_dec_min"))
            dec_max = float(self.cleaned_data.get("coord_dec_max"))
            results = results.filter(coord_dec_min__lte=dec_max)
            results = results.filter(coord_dec_max__gte=dec_min)
        except TypeError:
            pass

        return results

    def filter_by_pixel_scale(self, results):
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

    def filter_by_remote_source(self, results):
        remote_source = self.cleaned_data.get("remote_source")

        if remote_source is not None and remote_source != "":
            results = results.filter(remote_source=remote_source)

        return results

    def filter_by_subject_type(self, results):
        subject_type = self.cleaned_data.get("subject_type")

        if subject_type in vars(SubjectType).keys():
            results = results.filter(subject_type_char=subject_type)
        elif subject_type in vars(SolarSystemSubject).keys():
            results = results.filter(solar_system_main_subject_char=subject_type)

        return results

    def filter_by_telescope_type(self, results):
        telescope_type = self.cleaned_data.get("telescope_type")

        if telescope_type is not None and telescope_type != "":
            types = telescope_type.split(',')
            results = results.filter(telescope_types__in=types)

        return results

    def filter_by_integration_time(self, results):
        try:
            min = float(self.cleaned_data.get("integration_time_min"))
            results = results.filter(integration__gte=min * 3600)
        except TypeError:
            pass

        try:
            max = float(self.cleaned_data.get("integration_time_max"))
            results = results.filter(integration__lte=max * 3600)
        except TypeError:
            pass

        return results

    def filter_by_constellation(self, results):
        constellation = self.cleaned_data.get("constellation")

        if constellation is not None and constellation != "":
            results = results.filter(constellation="__%s__" % constellation)

        return results

    def filter_by_subject(self, results):
        subject = self.cleaned_data.get("subject")

        if subject is not None and subject != "":
            catalog_entries = []

            regex = r"(?P<catalog>M|NGC|IC)(?P<id>\d+)"
            matches = re.finditer(regex, subject, re.IGNORECASE)

            for matchNum, match in enumerate(matches, start=1):
                catalog_entries.append(match.string)

                groups = match.groups()
                catalog_entries.append("%s %s" % (groups[0], groups[1]))

            if catalog_entries:
                query = reduce(or_, (Q(objects_in_field=x) for x in catalog_entries))
                results = results.filter(query)
            else:
                results = results.filter(objects_in_field=CustomContain(subject))

        return results

    def filter_by_telescope(self, results):
        telescope = self.cleaned_data.get("telescope")

        if telescope is not None and telescope != "":
            results = results.filter(imaging_telescopes=CustomContain(telescope))

        return results

    def filter_by_camera(self, results):
        camera = self.cleaned_data.get("camera")

        if camera is not None and camera != "":
            results = results.filter(imaging_cameras=CustomContain(camera))

        return results

    def filter_by_bortle_scale(self, results):
        try:
            min = float(self.cleaned_data.get("bortle_scale_min"))
            results = results.filter(bortle_scale__gte=min)
        except TypeError:
            pass

        try:
            max = float(self.cleaned_data.get("bortle_scale_max"))
            results = results.filter(bortle_scale__lte=max)
        except TypeError:
            pass

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
        domain = self.cleaned_data.get('d')

        try:
            q = unicodedata.normalize('NFKD', q).encode('ascii', 'ignore')
        except:
            pass

        if q is None or q == u"":
            sqs = SearchQuerySet().all()
        else:
            if domain == 'u':
                sqs = self.searchqueryset.filter(text=CustomContain(q))
            else:
                sqs = self.searchqueryset.auto_query(q)

        sqs = self.filter_by_domain(sqs)

        # Images
        sqs = self.filter_by_type(sqs)
        sqs = self.filter_by_animated(sqs)
        sqs = self.filter_by_award(sqs)
        sqs = self.filter_by_camera_type(sqs)
        sqs = self.filter_by_country(sqs)
        sqs = self.filter_by_acquisition_type(sqs)
        sqs = self.filter_by_data_source(sqs)
        sqs = self.filter_by_date_published(sqs)
        sqs = self.filter_by_date_acquired(sqs)
        sqs = self.filter_by_license(sqs)
        sqs = self.filter_by_field_radius(sqs)
        sqs = self.filter_by_minimum_data(sqs)
        sqs = self.filter_by_moon_phase(sqs)
        sqs = self.filter_by_coords(sqs)
        sqs = self.filter_by_pixel_scale(sqs)
        sqs = self.filter_by_remote_source(sqs)
        sqs = self.filter_by_subject_type(sqs)
        sqs = self.filter_by_telescope_type(sqs)
        sqs = self.filter_by_integration_time(sqs)
        sqs = self.filter_by_constellation(sqs)
        sqs = self.filter_by_subject(sqs)
        sqs = self.filter_by_telescope(sqs)
        sqs = self.filter_by_camera(sqs)
        sqs = self.filter_by_bortle_scale(sqs)

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
