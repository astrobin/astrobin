from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType

from astrobin.models import (
    Comment,
)

from nested_comments.models import NestedComment

class Command(BaseCommand):
    help = "Migrate old comments to the nested_comments app."

    def handle(self, *args, **options):
        count = 0
        id_mapping = {}
        image_comments = Comment.objects.all().order_by('pk');
        for i in image_comments:
            nc = NestedComment(
                content_type = ContentType.objects.get(model = "image"),
                object_id = i.image.id,
                author = i.author,
                text = i.comment,
                created = i.added,
                updated = i.added,
                deleted = i.is_deleted,
            )

            if i.parent:
                try:
                    parent = NestedComment.objects.get(
                        id = id_mapping[i.parent.id]);
                    nc.parent = parent
                except NestedComment.DoesNotExist:
                    print "Could not find parent!"
                    return;

            nc.save()
            id_mapping[i.id] = nc.id
            count += 1

        print "Processed %d comments." % count
