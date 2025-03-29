from typing import Set

from django.db.models import QuerySet
from django.utils import timezone

from astrobin.models import Collection, Image


class CollectionService(object):
    collection = None

    def __init__(self, collection: Collection):
        self.collection = collection

    def add_remove_images(self, images: QuerySet):
        now = timezone.now()

        before = Image.objects_including_wip.filter(collections=self.collection)

        removed = before.exclude(pk__in=images.values_list('pk', flat=True))
        added = images.exclude(pk__in=before.values_list('pk', flat=True))

        removed.update(updated=now)
        added.update(updated=now)

        for x in removed:
            x.collections.remove(self.collection)
            x.collections.filter(cover=x).update(cover=None)

        for x in added:
            x.collections.add(self.collection)
            
        self.collection.update_counts(save=False)
        self.collection.update_cover()

    def get_descendant_collections(self, descendants=None) -> Set[Collection]:
        if descendants is None:
            descendants = set()

        descendants.add(self.collection)

        for child in self.collection.children.all():
            CollectionService(child).get_descendant_collections(descendants)

        return descendants
