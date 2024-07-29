import re
from enum import Enum
from functools import reduce

from django.db.models import Q
from haystack.backends import SQ
from haystack.inputs import BaseInput, Clean
from operator import and_, or_

from haystack.query import SearchQuerySet


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
        acquisition_months = data.get("acquisition_months")
        acquisition_months_op = data.get("acquisition_months_op")

        if acquisition_months_op == MatchType.ALL.value:
            op = and_
        else:
            op = or_

        if acquisition_months is not None and acquisition_months != "":
            months = acquisition_months.split(',')
            queries = []

            for month in months:
                queries.append(Q(acquisition_months=month))

            if len(queries) > 0:
                results = results.filter(reduce(op, queries))

        return results
