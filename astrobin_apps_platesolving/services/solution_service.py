from django.db.models import QuerySet
from django.urls import reverse

from astrobin.models import ImageRevision, Image
from astrobin_apps_platesolving.models import Solution, PlateSolvingAdvancedSettings


class SolutionService:
    solution = None  # type: Solution

    @staticmethod
    def get_or_create_advanced_settings(target):
        # type: (Union[Image, ImageRevision]) -> (PlateSolvingAdvancedSettings, bool)

        if target._meta.model_name == u'image':
            images = Image.objects_including_wip.filter(user=target.user).order_by('-pk')  # type: QuerySet[Image]
            for image in images:
                if image.solution and image.solution.advanced_settings:
                    latest_settings = image.solution.advanced_settings  # type: PlateSolvingAdvancedSettings
                    latest_settings.pk = None
                    latest_settings.sample_raw_frame_file = None
                    latest_settings.save()
                    return latest_settings, False
        elif target.image.solution and target.image.solution.advanced_settings:
            latest_settings = target.image.solution.advanced_settings
            latest_settings.pk = None
            latest_settings.save()
            return latest_settings, False

        return PlateSolvingAdvancedSettings.objects.create(), True

    def __init__(self, solution):
        # type: (Solution) -> None

        self.solution = solution

    def get_objects_in_field(self):
        # type: () -> List[str]

        objects = []
        if self.solution.objects_in_field:
            objects = [x.strip() for x in self.solution.objects_in_field.split(',')]
        if self.solution.advanced_annotations:
            advanced_annotations_lines = self.solution.advanced_annotations.split('\n')
            for line in advanced_annotations_lines:
                advanced_annotation = line.split(',')[-1]
                header = line.split(',')[0]
                if header == "Label" and advanced_annotation not in objects and advanced_annotation != '':
                    objects.append(advanced_annotation)

        return sorted(objects)

    def get_search_query_around(self, degrees):
        # type: (int) -> str
        ra = float(self.solution.advanced_ra or self.solution.ra)
        dec = float(self.solution.advanced_dec or self.solution.dec)

        ra_min = ra - degrees * .5
        ra_max = ra + degrees * .5

        dec_min = dec - degrees * .5
        dec_max = dec + degrees * .5

        field_min = 0
        field_max = degrees

        base_search_url = reverse('haystack_search')

        return base_search_url + \
               "?q=&d=i&t=all" + \
               "&coord_ra_min=%.2f&coord_ra_max=%.2f" % (ra_min, ra_max) + \
               "&coord_dec_min=%.2f&coord_dec_max=%.2f" % (dec_min, dec_max) + \
               "&field_radius_min=%.2f&field_radius_max=%.2f" % (field_min, field_max)
