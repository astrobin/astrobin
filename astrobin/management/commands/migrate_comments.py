from optparse import make_option

from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType

from astrobin.models import (
    Comment,
    GearComment,
)

from nested_comments.models import NestedComment

class Command(BaseCommand):
    help = "Migrate old comments to the nested_comments app."
    option_list = BaseCommand.option_list + (
        make_option(
            '--delete',
            action = 'store_true',
            default = False,
            dest = 'delete',
            help = "Deletes all the nested comments first"),
    )

    def handle(self, *args, **options):
        if options.get('delete'):
            NestedComment.objects.all().delete()
            print "Deleted all nested comments, as requested."

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

        id_mapping = {}
        gear_comments = GearComment.objects.all().order_by('pk');
        for i in gear_comments:
            nc = NestedComment(
                content_type = ContentType.objects.get(model = "gear"),
                object_id = i.gear.id,
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
