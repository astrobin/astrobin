from django.contrib.contenttypes.models import ContentType

from astrobin.tests.generators import Generators
from nested_comments.models import NestedComment


class NestedCommentsGenerators:
    def __init__(self):
        pass

    @staticmethod
    def comment(**kwargs):
        author = kwargs.pop('author', Generators.user())
        target = kwargs.pop('target', None)

        if target is None:
            target = Generators.image()

        return NestedComment.objects.create(
            author=author,
            content_type=ContentType.objects.get_for_model(target),
            object_id=target.id,
            text=Generators.randomString(),
        )
