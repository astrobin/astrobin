from django.db.models import QuerySet
from django.utils import timezone

from astrobin.models import Collection


class CollectionService(object):
    collection = None

    def __init__(self, collection: Collection):
        self.collection = collection

    def add_remove_images(self, images: QuerySet):
        now = timezone.now()

        before = self.collection.images.all()

        removed = before.exclude(pk__in=images.values_list('pk', flat=True))
        added = images.exclude(pk__in=before.values_list('pk', flat=True))

        removed.update(updated=now)
        added.update(updated=now)

        self.collection.images.remove(*removed)
        self.collection.images.add(*added)


