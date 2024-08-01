import re
from enum import Enum
from functools import reduce
from typing import Optional, Union

from django.db.models import Q
from haystack.backends import SQ
from haystack.inputs import BaseInput, Clean
from operator import and_, or_

from haystack.query import SearchQuerySet

from astrobin.enums import SolarSystemSubject, SubjectType
from astrobin_apps_equipment.models.sensor_base_model import ColorOrMono


class MatchType(Enum):
    ALL = 'ALL'
    ANY = 'ANY'


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

    def apply_boolean_filter(data: dict, results: SearchQuerySet, param_name: str, filter_attr: str) -> SearchQuerySet:
        value = SearchService.get_boolean_filter_value(data.get(param_name))
        if value is None:
            return results
        return results.filter(**{filter_attr: value})

    @staticmethod
    def filter_by_subject(data, results: SearchQuerySet) -> SearchQuerySet:
        subject = data.get("subject")
        q = data.get("q")

        if subject is not None and subject != "":
            if list(SearchService.find_catalog_subjects(subject)):
                results = SearchService.filter_by_subject_text(results, subject)
            else:
                results = results.filter(objects_in_field=CustomContain(subject))

        if q is not None and q != "":
            if list(SearchService.find_catalog_subjects(q)):
                results |= SearchService.filter_by_subject_text(results, q)

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

        pattern = r"(?P<catalog>Messier|M|NGC|IC|PGC|LDN|LBN|SH2_)\s?(?P<id>\d+)"
        return re.finditer(pattern, text, re.IGNORECASE)

    @staticmethod
    def filter_by_subject_text(results: SearchQuerySet, text: str) -> SearchQuerySet:
        if text is not None and text != "":
            catalog_entries = []
            matches = SearchService.find_catalog_subjects(text)

            for matchNum, match in enumerate(matches, start=1):
                groups = match.groups()
                catalog_entries.append("%s %s" % (groups[0], groups[1]))

            for entry in catalog_entries:
                results = results.narrow(f'objects_in_field:"{entry}"')

        return results

    @staticmethod
    def filter_by_telescope(data, results: SearchQuerySet) -> SearchQuerySet:
        telescope = data.get("telescope")

        if not telescope:
            return results

        try:
            telescope_id = int(telescope)
        except (ValueError, TypeError):
            telescope_id = None

        if isinstance(telescope, dict):
            telescope_id = telescope.get("id")
            telescope = telescope.get("name")

        if telescope_id and telescope_id != "":
            return results.filter(imaging_telescopes_2_id=telescope_id)

        if telescope and telescope != "":
            return results.filter(
                SQ(imaging_telescopes=CustomContain(telescope)) |
                SQ(imaging_telescopes_2=CustomContain(telescope))
            )

        return results

    @staticmethod
    def filter_by_camera(data, results: SearchQuerySet) -> SearchQuerySet:
        camera = data.get("camera")

        if not camera:
            return results

        try:
            camera_id = int(camera)
        except (ValueError, TypeError):
            camera_id = None

        if isinstance(camera, dict):
            camera_id = camera.get("id")
            camera = camera.get("name")

        if camera_id and camera_id != "":
            return results.filter(imaging_cameras_2_id=camera_id)

        if camera and camera != "":
            return results.filter(
                SQ(imaging_cameras=CustomContain(camera)) |
                SQ(imaging_cameras_2=CustomContain(camera))
            )

        return results

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
        if isinstance(data.get("acquisition_months"), dict):
            acquisition_months = data.get("acquisition_months").get("months")
            acquisition_months_op = data.get("acquisition_months").get("matchType")
        else:
            acquisition_months = data.get("acquisition_months")
            acquisition_months_op = data.get("acquisition_months_op")

        if acquisition_months_op == MatchType.ALL.value:
            op = and_
        else:
            op = or_

        if acquisition_months is not None and acquisition_months != "":
            if isinstance(acquisition_months, str):
                months = acquisition_months.split(',')
            else:
                months = acquisition_months

            queries = []

            for month in months:
                queries.append(Q(acquisition_months=month))

            if len(queries) > 0:
                results = results.filter(reduce(op, queries))

        return results

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
    def filter_by_color_or_mono(data, results: SearchQuerySet) -> SearchQuerySet:
        if isinstance(data.get("color_or_mono"), dict):
            value = data.get("color_or_mono").get("value")
            color_or_mono_op = data.get("color_or_mono").get("matchType")
        else:
            value = data.get("color_or_mono")
            color_or_mono_op = data.get("color_or_mono_op")
        queries = []

        if color_or_mono_op == MatchType.ALL.value:
            op = and_
        else:
            op = or_

        if value is not None and value != "":
            if isinstance(value, str):
                value = value.split(',')

            if ColorOrMono.COLOR.value in value:
                queries.append(Q(has_color_camera=True))

            if ColorOrMono.MONO.value in value:
                queries.append(Q(has_mono_camera=True))

        if len(queries) > 0:
            results = results.filter(reduce(op, queries))

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
