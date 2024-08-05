from datetime import datetime, timedelta
from functools import reduce
from operator import and_, or_

from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from haystack import connections
from haystack.backends import SQ
from haystack.forms import SearchForm
from haystack.generic_views import SearchView
from haystack.query import SearchQuerySet
from pybb.models import Post, Topic

from astrobin_apps_equipment.models.sensor_base_model import ColorOrMono
from astrobin_apps_groups.models import Group
from common.services.search_service import CustomContain, MatchType, SearchService
from common.templatetags.common_tags import asciify
from nested_comments.models import NestedComment
from .models import Image

FIELDS = (
    # Filtering
    'q',
    'd',
    't',
    'animated',
    'video',
    'award',
    'groups',
    'camera_type',
    'camera_pixel_size_min',
    'camera_pixel_size_max',
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
    'telescope_diameter_min',
    'telescope_diameter_max',
    'telescope_weight_min',
    'telescope_weight_max',
    'telescope_focal_length_min',
    'telescope_focal_length_max',
    'mount_weight_min',
    'mount_weight_max',
    'mount_max_payload_min',
    'mount_max_payload_max',
    'integration_time_min',
    'integration_time_max',
    'constellation',
    'subject',
    'telescope',
    'camera',
    'bortle_scale_min',
    'bortle_scale_max',
    'w_min',
    'w_max',
    'h_min',
    'h_max',
    'size_min',
    'size_max',
    'modified_camera',
    'color_or_mono',
    'color_or_mono_op',
    'topic',
    'filter_types',
    'filter_types_op',
    'user_id',
    'acquisition_months',
    'acquisition_months_op',
    'username',
    'telescope_ids',
    'camera_ids',
    'mount_ids',
    'filter_ids',
    'accessory_ids',
    'software_ids',

    # Sorting
    'sort'
)


class AstroBinSearchForm(SearchForm):
    # q is inherited from the parent form.

    d = forms.CharField(required=False)
    t = forms.CharField(required=False)

    animated = forms.BooleanField(required=False)
    video = forms.BooleanField(required=False)
    award = forms.CharField(required=False)
    groups = forms.CharField(required=False)
    camera_type = forms.CharField(required=False)
    camera_pixel_size_min = forms.FloatField(required=False)
    camera_pixel_size_max = forms.FloatField(required=False)
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
    telescope_diameter_min = forms.IntegerField(required=False)
    telescope_diameter_max = forms.IntegerField(required=False)
    telescope_weight_min = forms.FloatField(required=False)
    telescope_weight_max = forms.FloatField(required=False)
    telescope_focal_length_min = forms.IntegerField(required=False)
    telescope_focal_length_max = forms.IntegerField(required=False)
    mount_weight_min = forms.FloatField(required=False)
    mount_weight_max = forms.FloatField(required=False)
    mount_max_payload_min = forms.FloatField(required=False)
    mount_max_payload_max = forms.FloatField(required=False)
    integration_time_min = forms.FloatField(required=False)
    integration_time_max = forms.FloatField(required=False)
    constellation = forms.CharField(required=False)
    subject = forms.CharField(required=False)
    telescope = forms.CharField(required=False)
    camera = forms.CharField(required=False)
    bortle_scale_min = forms.FloatField(required=False)
    bortle_scale_max = forms.FloatField(required=False)
    w_min = forms.IntegerField(required=False)
    w_max = forms.IntegerField(required=False)
    h_min = forms.IntegerField(required=False)
    h_max = forms.IntegerField(required=False)
    size_min = forms.IntegerField(required=False)
    size_max = forms.IntegerField(required=False)
    modified_camera = forms.CharField(required=False)
    color_or_mono = forms.CharField(required=False)
    color_or_mono_op = forms.CharField(required=False)
    topic = forms.IntegerField(required=False)
    filter_types = forms.CharField(required=False)
    filter_types_op = forms.CharField(required=False)
    user_id = forms.IntegerField(required=False)
    acquisition_months = forms.CharField(required=False)
    acquisition_months_op = forms.CharField(required=False)
    username = forms.CharField(required=False)

    # For precise ID based equipment search
    telescope_ids = forms.CharField(required=False)
    camera_ids = forms.CharField(required=False)
    mount_ids = forms.CharField(required=False)
    filter_ids = forms.CharField(required=False)
    accessory_ids = forms.CharField(required=False)
    software_ids = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super(AstroBinSearchForm, self).__init__(args, kwargs)
        self.data = {x: kwargs.pop(x, None) for x in FIELDS}
        self.request = kwargs.pop('request')

    def filter_by_domain(self, results):
        d = self.cleaned_data.get("d")

        # i = Images
        # b = Bookmarked images
        # l = Liked images
        # u = Users
        # f = Forums
        # c = Comments

        if d is None or d == "":
            d = "i"

        if d == "i":
            results = results.models(Image)
        elif d == "iu":
            if not self.request.user.is_authenticated:
                raise PermissionDenied
            results = results.models(Image).filter(Q(username=self.request.user.username))
        elif d == "ib":
            if not self.request.user.is_authenticated:
                raise PermissionDenied
            results = results.models(Image).filter(bookmarked_by=self.request.user.pk)
        elif d == "il":
            if not self.request.user.is_authenticated:
                raise PermissionDenied
            results = results.models(Image).filter(liked_by=self.request.user.pk)
        elif d == "if":
            if not self.request.user.is_authenticated:
                raise PermissionDenied
            results = results.models(Image).filter(user_followed_by=self.request.user.pk)
        elif d == "u":
            results = results.models(User)
        elif d == "f":
            results = results.models(Post, Topic)
        elif d == "c":
            results = results.models(NestedComment)

        return results

    def filter_by_type(self, results):
        t = self.cleaned_data.get("t")
        q = self.cleaned_data.get('q')

        if t is None or t == "":
            t = "all"

        if t == 'imaging_cameras':
            results = results.filter(
                SQ(imaging_cameras=CustomContain(q)) |
                SQ(imaging_cameras_2=CustomContain(q))
            )
        elif t == 'imaging_telescopes':
            results = results.filter(
                SQ(imaging_telescopes=CustomContain(q)) |
                SQ(imaging_telescopes_2=CustomContain(q))
            )
        elif t == 'guiding_cameras':
            results = results.filter(
                SQ(guiding_cameras=CustomContain(q)) |
                SQ(guiding_cameras_2=CustomContain(q))
            )
        elif t == 'guiding_telescopes':
            results = results.filter(
                SQ(guiding_telescopes=CustomContain(q)) |
                SQ(guiding_telescopes_2=CustomContain(q))
            )
        elif t == 'mounts':
            results = results.filter(
                SQ(mounts=CustomContain(q)) |
                SQ(mounts_2=CustomContain(q))
            )
        elif t != "all":
            results = results.filter(**{t: self.cleaned_data.get('q')})

        return results

    def filter_by_groups(self, results):
        groups = self.cleaned_data.get("groups")
        queries = []

        if groups is not None and groups != "":
            pks = groups.split(',')
            if len(pks) > 0:
                groups = Group.objects.filter(pk__in=pks)
                for group in groups:
                    if self.request.user in group.members.all():
                        queries.append(Q(groups=CustomContain(f'_{group.pk}__')))

        if len(queries) > 0:
            results = results.filter(reduce(or_, queries))

        return results

    def filter_by_date_published(self, results):
        date_published_min = self.cleaned_data.get("date_published_min")
        date_published_max = self.cleaned_data.get("date_published_max")

        try:
            if date_published_min is not None and date_published_min != "":
                results = results.filter(published__gte=date_published_min)

            if date_published_max is not None and date_published_max != "":
                results = results.filter(
                    published__lt=datetime.strptime(date_published_max, '%Y-%m-%d') + timedelta(1)
                )
        except ValueError:
            pass

        return results

    def filter_by_date_acquired(self, results):
        date_acquired_min = self.cleaned_data.get("date_acquired_min")
        date_acquired_max = self.cleaned_data.get("date_acquired_max")

        try:
            if date_acquired_min is not None and date_acquired_min != "":
                results = results.filter(first_acquisition_date__gte=date_acquired_min)

            if date_acquired_max is not None and date_acquired_max != "":
                results = results.filter(
                    last_acquisition_date__lt=datetime.strptime(date_acquired_max, '%Y-%m-%d') + timedelta(1)
                )
        except ValueError:
            pass

    def filter_by_acquisition_type(self, results):
        acquisition_type = self.cleaned_data.get("acquisition_type")

        if acquisition_type is not None and acquisition_type != "":
            results = results.filter(acquisition_type=acquisition_type)

        return results

    def filter_by_w(self, results):
        try:
            min = int(self.cleaned_data.get("w_min"))
            results = results.filter(w__gte=min)
        except TypeError:
            pass

        try:
            max = int(self.cleaned_data.get("w_max"))
            results = results.filter(w__lte=max)
        except TypeError:
            pass

        return results

    def filter_by_h(self, results):
        try:
            min = int(self.cleaned_data.get("h_min"))
            results = results.filter(h__gte=min)
        except TypeError:
            pass

        try:
            max = int(self.cleaned_data.get("h_max"))
            results = results.filter(h__lte=max)
        except TypeError:
            pass

        return results

    def filter_by_forum_topic(self, results):
        topic = self.cleaned_data.get("topic")

        if topic is not None and topic != "":
            results = results.models(Post).filter(topic_id=topic)

        return results

    def filter_by_user_id(self, results):
        user_id = self.cleaned_data.get("user_id")

        if user_id is not None and user_id != "":
            results = results.filter(user_id=user_id)

        return results

    def filter_by_username(self, results):
        username = self.cleaned_data.get("username")

        if username is not None and username != "":
            results = results.filter(username=username)

        return results

    def filter_by_equipment_ids(self, results):
        telescope_ids = self.cleaned_data.get("telescope_ids")
        camera_ids = self.cleaned_data.get("camera_ids")
        mount_ids = self.cleaned_data.get("mount_ids")
        filter_ids = self.cleaned_data.get("filter_ids")
        accessory_ids = self.cleaned_data.get("accessory_ids")
        software_ids = self.cleaned_data.get("software_ids")

        if telescope_ids is not None and telescope_ids != "":
            results = results.filter(
                reduce(
                    or_, [
                        Q(imaging_telescopes_2_id=x) | Q(guiding_telescopes_2_id=x)
                        for x in telescope_ids.split(',')
                    ]
                )
            )

        if camera_ids is not None and camera_ids != "":
            results = results.filter(
                reduce(
                    or_, [
                        Q(imaging_cameras_2_id=x) | Q(guiding_cameras_2_id=x)
                        for x in camera_ids.split(',')
                    ]
                )
            )
        if mount_ids is not None and mount_ids != "":
            results = results.filter(
                reduce(
                    or_, [
                        Q(mounts_2_id=x)
                        for x in mount_ids.split(',')
                    ]
                )
            )

        if filter_ids is not None and filter_ids != "":
            results = results.filter(
                reduce(
                    or_, [
                        Q(filters_2_id=x)
                        for x in filter_ids.split(',')
                    ]
                )
            )

        if accessory_ids is not None and accessory_ids != "":
            results = results.filter(
                reduce(
                    or_, [
                        Q(accessories_2_id=x)
                        for x in accessory_ids.split(',')
                    ]
                )
            )

        if software_ids is not None and software_ids != "":
            results = results.filter(
                reduce(
                    or_, [
                        Q(software_2_id=x)
                        for x in software_ids.split(',')
                    ]
                )
            )

        return results

    def sort(self, results):
        order_by = None
        domain = self.cleaned_data.get('d', 'i')

        # Default to upload order for images.
        if domain.startswith('i'):
            order_by = ('-published', '-uploaded')

        # Default to updated/created order for comments/forums.
        if domain in ('c', 'f'):
            order_by = ('-updated', '-created')

        # Prefer user's choice of course.
        if self.data.get('sort') is not None:
            order_by = self.data.get('sort')

            # Special fixes for some fields.
            if order_by.endswith('field_radius'):
                results = results.exclude(_missing_='field_radius')
            elif order_by.endswith('pixel_scale'):
                results = results.exclude(_missing_='pixel_scale')
            elif order_by.endswith('coord_ra_min'):
                results = results.exclude(_missing_='coord_ra_min')
            elif order_by.endswith('coord_dec_min'):
                results = results.exclude(_missing_='coord_dec_min')

        if order_by not in ('', None):
            if type(order_by) is list or type(order_by) is tuple:
                results = results.order_by(*order_by)
            else:
                results = results.order_by(order_by)

        return results

    def search(self):
        q = self.cleaned_data.get('q')
        domain = self.cleaned_data.get('d')

        q = asciify(q)

        if q is None or q == "":
            sqs = SearchQuerySet().all()
        else:
            if domain == 'u':
                sqs = self.searchqueryset.filter(text=CustomContain(q))
            else:
                sqs = self.searchqueryset.auto_query(q)

        sqs = self.filter_by_domain(sqs)

        # Images
        sqs = self.filter_by_type(sqs)
        sqs = SearchService.filter_by_animated(self.cleaned_data, sqs)
        sqs = SearchService.filter_by_video(self.cleaned_data, sqs)
        sqs = SearchService.filter_by_award(self.cleaned_data, sqs)
        sqs = self.filter_by_groups(sqs)
        sqs = SearchService.filter_by_camera_type(self.cleaned_data, sqs)
        sqs = SearchService.filter_by_camera_pixel_size(self.cleaned_data, sqs)
        sqs = SearchService.filter_by_country(self.cleaned_data, sqs)
        sqs = SearchService.filter_by_acquisition_type(self.cleaned_data, sqs)
        sqs = SearchService.filter_by_data_source(self.cleaned_data, sqs)
        sqs = SearchService.filter_by_date_published(self.cleaned_data, sqs)
        sqs = SearchService.filter_by_date_acquired(self.cleaned_data, sqs)
        sqs = SearchService.filter_by_license(self.cleaned_data, sqs)
        sqs = SearchService.filter_by_field_radius(self.cleaned_data, sqs)
        sqs = SearchService.filter_by_minimum_data(self.cleaned_data, sqs)
        sqs = SearchService.filter_by_moon_phase(self.cleaned_data, sqs)
        sqs = SearchService.filter_by_coords(self.cleaned_data, sqs)
        sqs = SearchService.filter_by_pixel_scale(self.cleaned_data, sqs)
        sqs = SearchService.filter_by_remote_source(self.cleaned_data, sqs)
        sqs = SearchService.filter_by_subject_type(self.cleaned_data, sqs)
        sqs = SearchService.filter_by_telescope_type(self.cleaned_data, sqs)
        sqs = SearchService.filter_by_telescope_diameter(self.cleaned_data, sqs)
        sqs = SearchService.filter_by_telescope_weight(self.cleaned_data, sqs)
        sqs = SearchService.filter_by_telescope_focal_length(self.cleaned_data, sqs)
        sqs = SearchService.filter_by_mount_weight(self.cleaned_data, sqs)
        sqs = SearchService.filter_by_mount_max_payload(self.cleaned_data, sqs)
        sqs = SearchService.filter_by_integration_time(self.cleaned_data, sqs)
        sqs = SearchService.filter_by_constellation(self.cleaned_data, sqs)
        sqs = SearchService.filter_by_subject(self.cleaned_data, sqs)
        sqs = SearchService.filter_by_telescope(self.cleaned_data, sqs)
        sqs = SearchService.filter_by_camera(self.cleaned_data, sqs)
        sqs = SearchService.filter_by_bortle_scale(self.cleaned_data, sqs)
        sqs = self.filter_by_w(sqs)
        sqs = self.filter_by_h(sqs)
        sqs = SearchService.filter_by_size(self.cleaned_data, sqs)
        sqs = SearchService.filter_by_modified_camera(self.cleaned_data, sqs)
        sqs = SearchService.filter_by_color_or_mono(self.cleaned_data, sqs)
        sqs = self.filter_by_forum_topic(sqs)
        sqs = SearchService.filter_by_filter_types(self.cleaned_data, sqs)
        sqs = self.filter_by_user_id(sqs)
        sqs = SearchService.filter_by_acquisition_months(self.cleaned_data, sqs)
        sqs = self.filter_by_username(sqs)
        sqs = self.filter_by_equipment_ids(sqs)

        sqs = self.sort(sqs)

        return sqs


class AstroBinSearchView(SearchView):
    query = None
    results = None
    form_class = AstroBinSearchForm

    def get_form(self, form_class=None):
        context = {'request': self.request}
        data = {x: self.request.GET.get(x, None) for x in FIELDS}

        context.update(data)

        return self.get_form_class()(**context)

    def get_context_data(self, **kwargs):
        context = super(AstroBinSearchView, self).get_context_data(**kwargs)
        context['object_list'] = self.queryset
        return context


def set_max_result_window(index_name: str, max_result_window_value: int):
    backend = connections['default'].get_backend()

    if hasattr(backend, 'conn'):
        es = backend.conn
    else:
        return

    body = {
        "index": {
            "max_result_window": max_result_window_value
        }
    }

    es.indices.put_settings(index=index_name, body=body)
