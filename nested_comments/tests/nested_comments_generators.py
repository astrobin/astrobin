from django.contrib.contenttypes.models import ContentType

from astrobin.tests.generators import Generators
from nested_comments.models import NestedComment


class NestedCommentsGenerators:
    def __init__(self):
        pass

    @staticmethod
    def comment(**kwargs):
        target = kwargs.pop('target', None)
        author = kwargs.pop('author', None)

        if target is None:
            target = Generators.image()

        if author is None:
            author = Generators.user()

        return NestedComment.objects.create(
            author=kwargs.pop('author', author),
            content_type=ContentType.objects.get_for_model(target),
            object_id=target.id,
            text=kwargs.pop('text', Generators.randomString()),
            parent=kwargs.pop('parent', None),
            pending_moderation=kwargs.pop('pending_moderation', None)
        )
