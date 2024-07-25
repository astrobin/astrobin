import re

from haystack.backends import SQ
from haystack.inputs import BaseInput, Clean


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
    def filter_by_subject(data, results):
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
    def filter_by_subject_text(results, text):
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
    def filter_by_telescope(data, results):
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
