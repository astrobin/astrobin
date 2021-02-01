from django.db.models import QuerySet

from astrobin.models import ImageRevision, Image
from astrobin_apps_platesolving.models import Solution, PlateSolvingAdvancedSettings


class SolutionService:    
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
