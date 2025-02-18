import re
from datetime import datetime, time
from enum import Enum
from functools import reduce
from typing import Any, Callable, Optional, Type, Union

from django.contrib.auth.models import User
from django.contrib.postgres.search import TrigramDistance
from django.db.models import Q
from haystack.backends import SQ
from haystack.inputs import BaseInput, Clean, Raw
from operator import and_, or_

from haystack.query import SearchQuerySet

from astrobin.enums import SolarSystemSubject, SubjectType
from astrobin.models import Image
from astrobin.utils import ra_minutes_to_degrees
from astrobin_apps_equipment.models import (
    EquipmentBrandListing, EquipmentItemListing,
    EquipmentItemMarketplaceListingLineItem,
)
from astrobin_apps_equipment.models.sensor_base_model import ColorOrMono
from astrobin_apps_equipment.types.marketplace_listing_type import MarketplaceListingType
from astrobin_apps_groups.models import Group
from astrobin_apps_images.services import ImageService
from common.services import DateTimeService


class MatchType(Enum):
    ALL = 'ALL'
    ANY = 'ANY',
    EXACT = 'EXACT'


class CustomContain(BaseInput):
    """
    An input type for making wildcard matches.
    """
    input_type_name = 'custom_contain'

    def prepare(self, query_obj):
        query_string = super(CustomContain, self).prepare(query_obj)
        try:
            query_string = query_string.decode('utf-8')
        except AttributeError:
            pass
        query_string = query_obj.clean(query_string)

        exact_bits = [Clean(bit).prepare(query_obj) for bit in query_string.split(' ') if bit]
        query_string = ' '.join(exact_bits)

        return '*{}*'.format(query_string)


class SearchService:
    @staticmethod
    def get_boolean_filter_value(value: Optional[Union[str, bool]]) -> Optional[int]:
        if value is None:
            return None

        if (
                value is True or
                isinstance(value, str) and (
                value.upper() == 'Y' or
                value == '1' or
                value.lower() == 'true'
        )
        ):
            return 1
        elif (
                value is False or
                isinstance(value, str) and (
                        value.upper() == 'N'
                        or value == '0'
                        or value.lower() == 'false'
                )
        ):
            return 0
        else:
            return None

    @staticmethod
    def apply_boolean_filter(
            data: dict,
            results: SearchQuerySet,
            param_name: str,
            filter_attr: str
    ) -> SearchQuerySet:
        value = SearchService.get_boolean_filter_value(data.get(param_name))
        if value is True or value == 1:
            return results.filter(**{filter_attr: value})
        return results

    @staticmethod
    def apply_range_filter(
            data: dict,
            results: SearchQuerySet,
            param_name: str,
            min_filter_attr: str,
            max_filter_attr: str = None,
            value_type: Type[Union[int, float, str]] = float,
            value_multiplier: Optional[Union[int, float, str]] = None
    ) -> SearchQuerySet:
        def get_adjusted_value(value: Union[int, float, str]) -> Optional[Union[int, float, datetime]]:
            try:
                # Parse the value if it's a date string in "YYYY-MM-DD" format
                if value_type == str and isinstance(value, str):
                    return datetime.strptime(value, "%Y-%m-%d")  # Convert string to datetime
                adjusted_value = value_type(value)
                if value_multiplier is not None:
                    adjusted_value *= value_type(value_multiplier)
                return adjusted_value
            except (TypeError, ValueError):
                return None

        def apply_filter(value: Union[int, float, str, datetime], filter_attr: str, operator: str) -> SearchQuerySet:
            adjusted_value = get_adjusted_value(value)

            # Handle the case where value is a date (for the max filter)
            if operator == '__lte' and isinstance(adjusted_value, datetime):
                # If time is not specified, append the end of the day time (23:59:59.99999)
                if adjusted_value.time() == time.min:  # Means only date is provided
                    adjusted_value = adjusted_value.replace(hour=23, minute=59, second=59, microsecond=999999)

            if adjusted_value is None or (isinstance(adjusted_value, str) and adjusted_value == ''):
                return results
            return results.filter(**{f'{filter_attr}{operator}': adjusted_value})

        # Apply the min and max filters based on the data
        if f'{param_name}_min' in data:
            results = apply_filter(data.get(f'{param_name}_min'), min_filter_attr, '__gte')

        if f'{param_name}_max' in data:
            results = apply_filter(data.get(f'{param_name}_max'), max_filter_attr, '__lte')

        # Handle dictionary-style filtering
        if param_name in data:
            try:
                value = data.get(param_name)
                if isinstance(value, dict):
                    results = apply_filter(value.get('min'), min_filter_attr, '__gte')
                    results = apply_filter(value.get('max'), max_filter_attr, '__lte')
            except (TypeError, AttributeError):
                pass

        return results

    @staticmethod
    def apply_match_type_filter(
            data: dict,
            results: SearchQuerySet,
            key: str,
            match_type_key: str,
            query_func: Callable[[Any], Q]
    ) -> SearchQuerySet:
        if isinstance(data.get(key), dict):
            values = data.get(key).get("value")
            match_type = data.get(key).get("matchType")
        else:
            values = data.get(key)
            match_type = data.get(match_type_key)

        if match_type == MatchType.ALL.value:
            op = and_
        else:
            op = or_

        if values is not None and values != "":
            if isinstance(values, str):
                values = values.split(',')

            queries = [query_func(value) for value in values]

            if queries:
                results = results.filter(reduce(op, queries))

        return results

    @staticmethod
    def apply_equipment_filter(
            data,
            results: SearchQuerySet,
            key: str,
            id_field: str,
            legacy_field: Optional[str],
            new_field: str
    ) -> SearchQuerySet:
        item = data.get(key)
        queries = []
        op = or_
        match_type = None
        exact_match = False  # Used for single items where match_type is not available.

        if not item:
            return results

        if isinstance(item, dict):
            items = item.get("value")
            item_ids = [x['id'] for x in items]
            match_type = item.get("matchType", MatchType.ALL.value)
            exact_match = item.get("exactMatch", False)
            op = or_ if match_type == MatchType.ANY.value else and_
        elif isinstance(item, list):
            item_ids = item
        else:
            item_ids = None

        if item_ids:
            if exact_match or match_type == MatchType.EXACT.value:
                # Build a term query for each ID.
                for item_id in item_ids:
                    queries.append(Q(**{id_field: item_id}))
                # Additional filter to ensure the count matches exactly.
                queries.append(Q(**{f"{id_field}_count": len(item_ids)}))
            else:
                for item_id in item_ids:
                    queries.append(Q(**{id_field: item_id}))
        elif isinstance(item, str):
            if legacy_field is not None:
                queries.append(
                    Q(**{legacy_field: CustomContain(item)}) |
                    Q(**{new_field: CustomContain(item)})
                )
            else:
                queries.append(
                    Q(**{new_field: CustomContain(item)})
                )

        if queries:
            results = results.filter(reduce(op, queries))

        return results

    @staticmethod
    def filter_by_subject(data, results: SearchQuerySet) -> SearchQuerySet:
        subject = data.get("subject")
        subjects = data.get("subjects")
        q = data.get("q")

        def _build_subject_query(text: str) -> SQ:
            subject_query = SQ()

            if text is not None and text != "":
                catalog_entries = []
                matches = SearchService.find_catalog_subjects(text)

                for match in matches:
                    groups = match.groups()
                    catalog_name = groups[0].lower()
                    catalog_id = groups[1]

                    if catalog_name == "sh2_":
                        subject_entry = f"{catalog_name}{catalog_id}"
                        title_entry = f"Sh2-{catalog_id}"
                    else:
                        subject_entry = f"{catalog_name} {catalog_id}"
                        title_entry = f"{catalog_name} {catalog_id}"

                    catalog_entries.append(dict(subject_entry=subject_entry, title_entry=title_entry))

                # Build the SQ object with the OR conditions
                for x in catalog_entries:
                    subject_query |= (
                            SQ(objects_in_field__exact=x.get('subject_entry')) |
                            SQ(title=Raw(f'"{x.get("title_entry")}"')) |
                            SQ(title=Raw(f'"{x.get("title_entry").replace(" ", "")}"'))
                    )

            return subject_query

        def _build_subject_filter(subject: str) -> SQ:
            """Build the SQ filter for a single subject."""
            if subject:
                if list(SearchService.find_catalog_subjects(subject)):
                    return _build_subject_query(subject)
                else:
                    return (
                            SQ(objects_in_field__exact=subject) |
                            SQ(title__icontains=subject) |
                            SQ(title__icontains=subject.replace(' ', ''))
                    )
            return SQ()

        def _build_multiple_subject_filters(subjects: list, match_type: str) -> SQ:
            """Build the SQ filters for multiple subjects with the specified match type (AND/OR)."""
            if match_type == MatchType.ANY.value:
                # Apply OR logic by combining SQ filters
                queries = [_build_subject_filter(subject) for subject in subjects]
                return reduce(or_, queries)
            else:
                # Apply AND logic by chaining SQ filters
                queries = [_build_subject_filter(subject) for subject in subjects]
                return reduce(and_, queries)

        # Handle the "subjects" input
        if subjects and isinstance(subjects, dict):
            subject_values = subjects.get("value", [])
            match_type = subjects.get("matchType", MatchType.ANY.value)
            results = results.filter(_build_multiple_subject_filters(subject_values, match_type))

        # Handle the "subject" input
        if subject:
            results = results.filter(_build_subject_filter(subject))

        # Handle the "q" input separately and combine using OR
        if q:
            q_filtered_results = results.narrow(_build_subject_filter(q))
            results = results | q_filtered_results

        return results

    @staticmethod
    def find_catalog_subjects(text: str):
        text = text \
            .lower() \
            .replace('sh2-', 'sh2_') \
            .replace('sh2 ', 'sh2_') \
            .replace('messier', 'm') \
            .replace('"', '') \
            .replace("'", '') \
            .strip()

        pattern = r"\b(?P<catalog>Messier|M|NGC|IC|PGC|LDN|LBN|SH2_|VDB)\s?(?P<id>\d+)"
        return re.finditer(pattern, text, re.IGNORECASE)

    @staticmethod
    def filter_by_telescope(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_equipment_filter(
            data,
            results,
            key="telescope",
            id_field="imaging_telescopes_2_id",
            legacy_field="imaging_telescopes",
            new_field="imaging_telescopes_2"
        )

    @staticmethod
    def filter_by_sensor(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_equipment_filter(
            data,
            results,
            key="sensor",
            id_field="imaging_sensors_id",
            legacy_field=None,
            new_field="imaging_sensors"
        )

    @staticmethod
    def filter_by_camera(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_equipment_filter(
            data,
            results,
            key="camera",
            id_field="imaging_cameras_2_id",
            legacy_field="imaging_cameras",
            new_field="imaging_cameras_2"
        )

    @staticmethod
    def filter_by_mount(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_equipment_filter(
            data,
            results,
            key="mount",
            id_field="mounts_2_id",
            legacy_field="mounts",
            new_field="mounts_2"
        )

    @staticmethod
    def filter_by_filter(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_equipment_filter(
            data,
            results,
            key="filter",
            id_field="filters_2_id",
            legacy_field="filters",
            new_field="filters_2"
        )

    @staticmethod
    def filter_by_accessory(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_equipment_filter(
            data,
            results,
            key="accessory",
            id_field="accessories_2_id",
            legacy_field="accessories",
            new_field="accessories_2"
        )

    @staticmethod
    def filter_by_software(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_equipment_filter(
            data,
            results,
            key="software",
            id_field="software_2_id",
            legacy_field="software",
            new_field="software_2"
        )

    @staticmethod
    def filter_by_telescope_types(data, results: SearchQuerySet) -> SearchQuerySet:
        def query_func(telescope_type):
            return Q(telescope_types=telescope_type)

        return SearchService.apply_match_type_filter(
            data,
            results,
            "telescope_types",
            "telescope_types_op",
            query_func
        )

    @staticmethod
    def filter_by_camera_types(data, results: SearchQuerySet) -> SearchQuerySet:
        def query_func(camera_type):
            return Q(camera_types=camera_type)

        return SearchService.apply_match_type_filter(
            data,
            results,
            "camera_types",
            "camera_types_op",
            query_func
        )

    @staticmethod
    def filter_by_telescope_type(data, results: SearchQuerySet) -> SearchQuerySet:
        telescope_type = data.get("telescope_type")

        if telescope_type is not None and telescope_type != "":
            types = telescope_type.split(',')
            results = results.filter(telescope_types__in=types)

        return results

    @staticmethod
    def filter_by_camera_type(data, results: SearchQuerySet) -> SearchQuerySet:
        camera_type = data.get("camera_type")

        if camera_type is not None and camera_type != "":
            types = camera_type.split(',')
            results = results.filter(camera_types__in=types)

        return results

    @staticmethod
    def filter_by_acquisition_months(data, results: SearchQuerySet) -> SearchQuerySet:
        def query_func(month):
            return Q(acquisition_months=month)

        return SearchService.apply_match_type_filter(
            data,
            results,
            "acquisition_months",
            "acquisition_months_op",
            query_func
        )

    @staticmethod
    def filter_by_filter_types(data: dict, results: SearchQuerySet) -> SearchQuerySet:
        def query_func(filter_type):
            return Q(filter_types=filter_type)

        return SearchService.apply_match_type_filter(
            data,
            results,
            "filter_types",
            "filter_types_op",
            query_func
        )

    @staticmethod
    def filter_by_color_or_mono(data, results: SearchQuerySet) -> SearchQuerySet:
        def query_func(value):
            if value == ColorOrMono.COLOR.value:
                return Q(has_color_camera=True)
            elif value == ColorOrMono.MONO.value:
                return Q(has_mono_camera=True)
            return Q()

        return SearchService.apply_match_type_filter(
            data,
            results,
            "color_or_mono",
            "color_or_mono_op",
            query_func
        )

    @staticmethod
    def filter_by_remote_source(data, results: SearchQuerySet) -> SearchQuerySet:
        remote_source = data.get("remote_source")

        if remote_source is not None and remote_source != "":
            results = results.filter(remote_source=remote_source)

        return results

    @staticmethod
    def filter_by_subject_type(data, results: SearchQuerySet) -> SearchQuerySet:
        subject_type = data.get("subject_type")

        if subject_type in list(vars(SubjectType).keys()):
            results = results.filter(subject_type_char=subject_type)
        elif subject_type in list(vars(SolarSystemSubject).keys()):
            results = results.filter(solar_system_main_subject_char=subject_type)

        return results

    @staticmethod
    def filter_by_modified_camera(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_boolean_filter(data, results, "modified_camera", "has_modified_camera")

    @staticmethod
    def filter_by_animated(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_boolean_filter(data, results, "animated", "animated")

    @staticmethod
    def filter_by_video(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_boolean_filter(data, results, "video", "video")

    @staticmethod
    def filter_by_award(data, results: SearchQuerySet) -> SearchQuerySet:
        award = data.get("award")

        queries = []

        if award is not None and award != "":
            if isinstance(award, str):
                types = award.split(',')
            else:
                types = award

            if "iotd" in types:
                queries.append(Q(is_iotd=True))

            if "top-pick" in types:
                queries.append(Q(is_top_pick=True))

            if "top-pick-nomination" in types:
                queries.append(Q(is_top_pick_nomination=True))

        if len(queries) > 0:
            results = results.filter(reduce(or_, queries))

        return results

    @staticmethod
    def filter_by_country(data, results: SearchQuerySet) -> SearchQuerySet:
        country = data.get("country")

        if country is not None and country != "":
            results = results.filter(countries=CustomContain('__%s__' % country))

        return results

    @staticmethod
    def filter_by_data_source(data, results: SearchQuerySet) -> SearchQuerySet:
        data_source = data.get("data_source")

        if data_source is not None and data_source != "":
            results = results.filter(data_source=data_source)

        return results

    @staticmethod
    def filter_by_minimum_data(data, results: SearchQuerySet) -> SearchQuerySet:
        minimum_data = data.get("minimum_data")

        if minimum_data is not None and minimum_data != "":
            if isinstance(minimum_data, str):
                minimum = minimum_data.split(',')
            else:
                minimum = minimum_data

            for data in minimum:
                if data == 't':
                    results = results.exclude(SQ(_missing_="imaging_telescopes") & SQ(_missing_="imaging_telescopes_2"))
                if data == "c":
                    results = results.exclude(SQ(_missing_="imaging_cameras") & SQ(_missing_="imaging_cameras_2"))
                if data == "a":
                    results = results.exclude(_missing_="first_acquisition_date")
                if data == "s":
                    results = results.exclude(_missing_="pixel_scale")

        return results

    @staticmethod
    def filter_by_constellation(data, results: SearchQuerySet) -> SearchQuerySet:
        constellation = data.get("constellation")

        if constellation is not None and constellation != "":
            results = results.filter(constellation="__%s__" % constellation)

        return results

    @staticmethod
    def filter_by_bortle_scale(data, results: SearchQuerySet) -> SearchQuerySet:
        if 'bortle_scale_min' in data:
            try:
                minimum = float(data.get('bortle_scale_min'))
                results = results.filter(bortle_scale__gte=minimum)
            except TypeError:
                return results

        if 'bortle_scale_max' in data:
            try:
                maximum = float(data.get('bortle_scale_max'))
                results = results.filter(bortle_scale__lte=maximum)
            except TypeError:
                return results

        if 'bortle_scale' in data:
            try:
                value = data.get('bortle_scale')
                minimum = float(value.get('min'))
                maximum = float(value.get('max'))
                results = results.filter(bortle_scale__gte=minimum, bortle_scale__lte=maximum)
            except (TypeError, AttributeError):
                return results

        return results

    @staticmethod
    def filter_by_license(data, results: SearchQuerySet) -> SearchQuerySet:
        licenses = data.get("licenses") or data.get("license")

        if licenses is not None and licenses != "":
            if isinstance(licenses, str):
                licenses = licenses.split(',')
            results = results.filter(license_name__in=licenses)

        return results

    @staticmethod
    def filter_by_camera_pixel_size(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_range_filter(
            data,
            results,
            'camera_pixel_size',
            'min_camera_pixel_size',
            'max_camera_pixel_size'
        )

    @staticmethod
    def filter_by_field_radius(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_range_filter(
            data,
            results,
            'field_radius',
            'field_radius',
            'field_radius'
        )

    @staticmethod
    def filter_by_pixel_scale(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_range_filter(
            data,
            results,
            'pixel_scale',
            'pixel_scale',
            'pixel_scale'
        )

    @staticmethod
    def filter_by_telescope_diameter(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_range_filter(
            data,
            results,
            'telescope_diameter',
            'min_aperture',
            'max_aperture',
            int
        )

    @staticmethod
    def filter_by_telescope_weight(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_range_filter(
            data,
            results,
            'telescope_weight',
            'min_telescope_weight',
            'max_telescope_weight'
        )

    @staticmethod
    def filter_by_mount_weight(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_range_filter(
            data,
            results,
            'mount_weight',
            'min_mount_weight',
            'max_mount_weight'
        )

    @staticmethod
    def filter_by_mount_max_payload(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_range_filter(
            data,
            results,
            'mount_max_payload',
            'min_mount_max_payload',
            'max_mount_max_payload'
        )

    @staticmethod
    def filter_by_telescope_focal_length(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_range_filter(
            data,
            results,
            'telescope_focal_length',
            'min_focal_length',
            'max_focal_length',
            int
        )

    @staticmethod
    def filter_by_integration_time(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_range_filter(
            data,
            results,
            'integration_time',
            'integration',
            'integration',
            value_multiplier=3600
        )

    @staticmethod
    def filter_by_size(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_range_filter(
            data,
            results,
            'size',
            'size',
            'size',
            int,
            value_multiplier=1e6
        )

    @staticmethod
    def filter_by_date_published(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_range_filter(
            data,
            results,
            'date_published',
            'published',
            'published',
            str
        )

    @staticmethod
    def filter_by_date_acquired(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_range_filter(
            data,
            results,
            'date_acquired',
            'last_acquisition_date',
            'last_acquisition_date',
            str
        )

    @staticmethod
    def filter_by_acquisition_type(data, results: SearchQuerySet) -> SearchQuerySet:
        acquisition_type = data.get("acquisition_type")

        if acquisition_type is not None and acquisition_type != "":
            results = results.filter(acquisition_type=acquisition_type)

        return results

    @staticmethod
    def filter_by_moon_phase(data, results: SearchQuerySet) -> SearchQuerySet:
        return SearchService.apply_range_filter(
            data,
            results,
            'moon_phase',
            'moon_phase',
            'moon_phase'
        )

    @staticmethod
    def filter_by_coords(data, results: SearchQuerySet) -> SearchQuerySet:
        # Intersection between the filter ra,dec area and the image area.
        try:
            ra_min = float(data.get("coord_ra_min"))
            ra_max = float(data.get("coord_ra_max"))
            results = results.filter(coord_ra_min__lte=ra_max)
            results = results.filter(coord_ra_max__gte=ra_min)
        except TypeError:
            pass

        try:
            dec_min = float(data.get("coord_dec_min"))
            dec_max = float(data.get("coord_dec_max"))
            results = results.filter(coord_dec_min__lte=dec_max)
            results = results.filter(coord_dec_max__gte=dec_min)
        except TypeError:
            pass

        try:
            coords = data.get("coords")
            if coords:
                ra_min = ra_minutes_to_degrees(float(coords.get("ra").get("min")))
                ra_max = ra_minutes_to_degrees(float(coords.get("ra").get("max")))
                dec_min = float(coords.get("dec").get("min"))
                dec_max = float(coords.get("dec").get("max"))
                results = results.filter(
                    coord_ra_min__lte=ra_max,
                    coord_ra_max__gte=ra_min,
                    coord_dec_min__lte=dec_max,
                    coord_dec_max__gte=dec_min
                )
        except (TypeError, AttributeError):
            pass

        return results

    @staticmethod
    def filter_by_image_size(data, results: SearchQuerySet) -> SearchQuerySet:
        try:
            width_min = int(data.get("w_min"))
            width_max = int(data.get("w_max"))
            results = results.filter(
                w__gte=width_min,
                w__lte=width_max
            )
        except (TypeError, ValueError):
            pass

        try:
            height_min = int(data.get("h_min"))
            height_max = int(data.get("h_max"))
            results = results.filter(
                h__gte=height_min,
                h__lte=height_max
            )
        except (TypeError, ValueError):
            pass

        try:
            image_size = data.get("image_size")
            if image_size:
                width_min = int(image_size.get("w").get("min"))
                width_max = int(image_size.get("w").get("max"))
                height_min = int(image_size.get("h").get("min"))
                height_max = int(image_size.get("h").get("max"))
                results = results.filter(
                    w__gte=width_min,
                    w__lte=width_max,
                    h__gte=height_min,
                    h__lte=height_max
                )
        except (TypeError, AttributeError):
            pass

        return results

    @staticmethod
    def filter_by_groups(data, user: User, results: SearchQuerySet) -> SearchQuerySet:
        groups = data.get("groups")
        queries = []
        op = or_

        def build_queries(pks):
            if len(pks) > 0:
                group_objects = Group.objects.filter(pk__in=pks)
                for group_object in group_objects.iterator():
                    if user in group_object.members.all():
                        queries.append(Q(groups=CustomContain(f'__{group_object.pk}__')))

        if groups is not None:
            if isinstance(groups, str) and groups != '':
                pks = groups.split(',')
                build_queries(pks)
            elif isinstance(groups, dict):
                pks = groups.get('value')
                match_type = groups.get('matchType')
                build_queries(pks)
                if match_type == MatchType.ALL.value:
                    op = and_
                else:
                    op = or_

        if len(queries) > 0:
            results = results.filter(reduce(op, queries))

        return results

    @staticmethod
    def filter_by_personal_filters(data, user: User, results: SearchQuerySet) -> SearchQuerySet:
        personal_filters = data.get("personal_filters")

        if personal_filters is None:
            return results

        value = personal_filters.get("value")

        # value is a list of strings. See if 'my_images' is in it.
        filter_my_images = "my_images" in value
        filter_my_likes = "my_likes" in value
        filter_my_bookmarks = "my_bookmarks" in value
        filter_my_followed_users = "my_followed_users" in value

        match_type = personal_filters.get("matchType", MatchType.ANY.value)

        op = match_type == MatchType.ALL.value and and_ or or_

        queries = []

        if filter_my_images:
            queries.append(Q(username=user.username))

        if filter_my_likes:
            queries.append(Q(liked_by=user.pk))

        if filter_my_bookmarks:
            queries.append(Q(bookmarked_by=user.pk))

        if filter_my_followed_users:
            queries.append(Q(user_followed_by=user.pk))

        if len(queries) > 0:
            results = results.filter(reduce(op, queries))

        return results

    @staticmethod
    def filter_by_equipment_ids(data, results: SearchQuerySet) -> SearchQuerySet:
        def apply_filter(results: SearchQuerySet, ids: str, query_templates: list) -> SearchQuerySet:
            if ids is not None and ids != "":
                queries = reduce(or_, [Q(**{template: x}) for x in ids.split(',') for template in query_templates])
                results = results.filter(queries)
            return results

        filters = [
            ("all_telescope_ids", ["imaging_telescopes_2_id", "guiding_telescopes_2_id"]),
            ("imaging_telescope_ids", ["imaging_telescopes_2_id"]),
            ("guiding_telescope_ids", ["guiding_telescopes_2_id"]),
            ("all_camera_ids", ["imaging_cameras_2_id", "guiding_cameras_2_id"]),
            ("imaging_camera_ids", ["imaging_cameras_2_id"]),
            ("guiding_camera_ids", ["guiding_cameras_2_id"]),
            ("all_sensor_ids", ["imaging_sensors_id", "guiding_sensors_id"]),
            ("imaging_sensor_ids", ["imaging_sensors_id"]),
            ("guiding_sensor_ids", ["guiding_sensors_id"]),
            ("mount_ids", ["mounts_2_id"]),
            ("filter_ids", ["filters_2_id"]),
            ("accessory_ids", ["accessories_2_id"]),
            ("software_ids", ["software_2_id"]),
        ]

        for key, query_templates in filters:
            results = apply_filter(results, data.get(key), query_templates)

        return results

    @staticmethod
    def filter_by_user_id(data, results: SearchQuerySet) -> SearchQuerySet:
        user_id = data.get("user_id")
        users = data.get("users")

        if user_id is not None and user_id != "":
            results = results.filter(user_id=user_id)
        elif users is not None:
            match_type = users.get('matchType')
            user_ids = [x.get('id') for x in users.get('value')]
            op = and_ if match_type == MatchType.ALL.value else or_
            results = results.filter(reduce(op, [(SQ(user_id=x) | SQ(collaborator_ids=x)) for x in user_ids]))

        return results

    @staticmethod
    def filter_by_username(data, results: SearchQuerySet) -> SearchQuerySet:
        username = data.get("username")

        if username is not None and username != "":
            results = results.filter(username=username)

        return results

    @staticmethod
    def filter_by_forum_topic(data, results: SearchQuerySet) -> SearchQuerySet:
        topic = data.get("topic")

        if topic is not None and topic != "":
            results = results.filter(topic_id=int(topic))

        return results

    @staticmethod
    def filter_by_similar_images(data, results: SearchQuerySet) -> SearchQuerySet:
        image_id = data.get("similar_to_image_id")

        if image_id is not None and image_id != "":
            image = ImageService.get_object(
                image_id,
                Image.objects_plain.only('id', 'subject_type', 'solar_system_main_subject')
            )

            if image is None:
                return results.none()

            if image.subject_type in (SubjectType.DEEP_SKY, SubjectType.WIDE_FIELD):
                if image.solution and image.solution.ra and image.solution.dec:
                    target_ra = float(image.solution.advanced_ra or image.solution.ra)
                    target_dec = float(image.solution.advanced_dec or image.solution.dec)
                    delta = float(image.solution.radius)

                    search_ra_min = target_ra - delta
                    search_ra_max = target_ra + delta
                    search_dec_min = target_dec - delta
                    search_dec_max = target_dec + delta
                    field_radius_min = delta / 4
                    field_radius_max = min(180.0, delta * 4)

                    results = results.filter(
                        coord_ra_min__lte=search_ra_max,
                        coord_ra_max__gte=search_ra_min,
                        coord_dec_min__lte=search_dec_max,
                        coord_dec_max__gte=search_dec_min,
                        field_radius__range=(field_radius_min, field_radius_max)
                    )
                else:
                    # No solution, let's see if there's a catalog name in the title.
                    title = image.title.lower()
                    matches = SearchService.find_catalog_subjects(title)
                    first_match = next(matches, None)
                    if first_match:
                        groups = first_match.groups()
                        catalog_entry = "%s %s" % (groups[0], groups[1])
                        results = results.filter(
                            SQ(title=CustomContain(catalog_entry)) |
                            SQ(objects_in_field=catalog_entry)
                        )
            elif image.subject_type in (
                    SubjectType.STAR_TRAILS,
                    SubjectType.NORTHERN_LIGHTS,
                    SubjectType.NOCTILUCENT_CLOUDS,
                    SubjectType.LANDSCAPE,
                    SubjectType.ARTIFICIAL_SATELLITE,
                    SubjectType.GEAR,
                    SubjectType.OTHER
            ):
                results = results.filter(subject_type_char=image.subject_type)
            elif image.subject_type == SubjectType.SOLAR_SYSTEM:
                results = results.filter(solar_system_main_subject_char=image.solar_system_main_subject)
            else:
                results = results.none()

            return results.exclude(SQ(object_id=image_id) | SQ(hash=image.hash))

        return results

    @staticmethod
    def filter_by_collaboration(data, results: SearchQuerySet) -> SearchQuerySet:
        collaboration = data.get("collaboration")

        if collaboration == 'true':
            results = results.exclude(_missing_="collaborator_ids")
        elif collaboration == 'false':
            results = results.filter(_missing_="collaborator_ids")

        return results

    @staticmethod
    def get_equipment_brand_listings(q: str, country: str):
        return EquipmentBrandListing.objects.annotate(
            distance=TrigramDistance('brand__name', q)
        ).filter(
            Q(
                Q(distance__lte=.85) |
                Q(brand__name__icontains=q)
            ) &
            Q(
                Q(retailer__countries__icontains=country) |
                Q(retailer__countries__isnull=True)
            )
        )

    @staticmethod
    def get_equipment_item_listings(q: str, country: str):
        return EquipmentItemListing.objects.annotate(
            distance=TrigramDistance('name', q)
        ).filter(
            Q(
                Q(distance__lte=.5) |
                Q(item_full_name__icontains=q)
            ) &
            Q(
                Q(retailer__countries__icontains=country) |
                Q(retailer__countries__isnull=True)
            )
        )

    @staticmethod
    def get_marketplace_line_items(q: str):
        return EquipmentItemMarketplaceListingLineItem.objects.annotate(
            distance=TrigramDistance('item_name', q)
        ).filter(
            Q(
                Q(distance__lte=.5) |
                Q(item_name__icontains=q)
            ),
            listing__listing_type=MarketplaceListingType.FOR_SALE.value,
            sold__isnull=True,
            listing__approved__isnull=False,
            listing__expiration__gt=DateTimeService.now(),
        )
