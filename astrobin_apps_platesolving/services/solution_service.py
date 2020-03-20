from astrobin_apps_platesolving.models import Solution


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
