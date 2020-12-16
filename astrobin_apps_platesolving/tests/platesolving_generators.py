from django.contrib.contenttypes.models import ContentType

from astrobin_apps_platesolving.models import Solution


class PlateSolvingGenerators:
    def __init__(self):
        pass

    @staticmethod
    def solution(target, *args, **kwargs):
        return Solution.objects.create(
            object_id=target.pk,
            content_type=ContentType.objects.get_for_model(target)
        )
