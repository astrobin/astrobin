# Python
import unicodedata

# Django
from django.contrib.auth.models import User

# Third party apps
from django.core.paginator import Paginator
from django.http import Http404
from haystack.query import SearchQuerySet
from haystack.generic_views import SearchView
from pybb.models import Post, Topic

from nested_comments.models import NestedComment

from models import Image


class AstroBinSearchView(SearchView):
    query = None
    results = None

    def filterByDomain(self, results):
        d = self.request.GET.get("d")

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
        t = self.request.GET.get("t")

        if t is None or t == "":
            t = "all"

        if t != "all":
            results = results.filter(**{t: self.query})

        return results

    def filterByAnimated(self, results):
        t = self.request.GET.get("animated")

        if t is not None:
            results = results.filter(animated=True)

        return results

    def filterByCameraType(self, results):
        camera_type = self.request.GET.get("camera_type")

        if camera_type is not None and camera_type != "":
            types = camera_type.split(',')
            results = results.filter(camera_types__in=types)

        return results

    def filterByCountry(self, results):
        country = self.request.GET.get("country")

        if country is not None and country != "":
            results = results.filter(countries=country)

        return results

    def filterByDataSource(self, results):
        data_source = self.request.GET.get("data_source")

        if data_source is not None:
            results = results.filter(data_source=data_source)

        return results

    def filterByFieldRadius(self, results):
        try:
            min = float(self.request.GET.get("field_radius_min"))
            results = results.filter(field_radius__gte=min)
        except TypeError:
            pass

        try:
            max = float(self.request.GET.get("field_radius_max"))
            results = results.filter(field_radius__lte=max)
        except TypeError:
            pass

        return results

    def filterByMinimumData(self, results):
        minimum_data = self.request.GET.get("minimum_data")

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
            min = float(self.request.GET.get("moon_phase_min"))
            results = results.filter(moon_phase__gte=min)
        except TypeError:
            pass

        try:
            max = float(self.request.GET.get("moon_phase_max"))
            results = results.filter(moon_phase__lte=max)
        except TypeError:
            pass

        return results

    def filterByLicense(self, results):
        license = self.request.GET.get("license")

        if license is not None and license != "":
            licenses = license.split(',')
            results = results.filter(license__in=licenses)

        return results

    def filterByPixelScale(self, results):
        try:
            min = float(self.request.GET.get("pixel_scale_min"))
            results = results.filter(pixel_scale__gte=min)
        except TypeError:
            pass

        try:
            max = float(self.request.GET.get("pixel_scale_max"))
            results = results.filter(pixel_scale__lte=max)
        except TypeError:
            pass

        return results

    def filterBySubjectType(self, results):
        subject_type = self.request.GET.get("subject_type")

        if subject_type == "deep_sky":
            results = results.filter(subject_type=100)
        elif subject_type == "solar_system":
            results = results.filter(subjec_type=200)
        elif subject_type == "wide":
            results = results.filter(subjec_type=300)
        elif subject_type == "trails":
            results = results.filter(subjec_type=400)
        elif subject_type == "aurora":
            results = results.filter(subjec_type=450)
        elif subject_type == "gear":
            results = results.filter(subjec_type=500)
        elif subject_type == "other":
            results = results.filter(subjec_type=600)
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
        telescope_type = self.request.GET.get("telescope_type")

        if telescope_type is not None and telescope_type != "":
            types = telescope_type.split(',')
            results = results.filter(telescope_types__in=types)

        return results

    def get_queryset(self):
        self.query = self.request.GET.get('q')
        try:
            self.query = unicodedata.normalize('NFKD', self.query).encode('ascii', 'ignore')
        except:
            pass

        if self.query is None or self.query == u"":
            self.results = SearchQuerySet().all()
        else:
            self.results = super(AstroBinSearchView, self).get_queryset().filter(text=self.query)

        self.results = self.filterByDomain(self.results)

        # Images
        self.results = self.filterByType(self.results)
        self.results = self.filterByAnimated(self.results)
        self.results = self.filterByCameraType(self.results)
        self.results = self.filterByCountry(self.results)
        self.results = self.filterByDataSource(self.results)
        self.results = self.filterByLicense(self.results)
        self.results = self.filterByFieldRadius(self.results)
        self.results = self.filterByMinimumData(self.results)
        self.results = self.filterByMoonPhase(self.results)
        self.results = self.filterByPixelScale(self.results)
        self.results = self.filterBySubjectType(self.results)
        self.results = self.filterByTelescopeType(self.results)

        order_by = None

        # Default to upload order for images.
        if  'd' not in self.request.GET or self.request.GET.get('d') == 'i':
            order_by = ('-published', '-uploaded')

        # Default to updated/created order for comments/forums.
        if self.request.GET.get('d') == 'cf':
            order_by = ('-updated', '-created')

        # Override with user choice of course.
        if 'sort' in self.request.GET:
            order_by = self.request.GET['sort']

            # Special fixes for some fields.
            if order_by.endswith('field_radius'):
                self.results = self.results.exclude(_missing_='field_radius')
            if order_by.endswith('pixel_scale'):
                self.results = self.results.exclude(_missing_='pixel_scale')

            # Make it a list that will be exploded into arguments here below.
            order_by = [order_by]

        if order_by is not None:
            self.results = self.results.order_by(*order_by)

        return self.results
