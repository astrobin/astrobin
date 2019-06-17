# Django
from django.db import models

# This app
from .folders import FOLDER_TYPE_LOOKUP


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super(SoftDeleteManager, self).get_queryset().filter(active=True)

    def all_with_inactive(self):
        return super(SoftDeleteManager, self).get_queryset()

    def get(self, *args, **kwargs):
        ''' if a specific record was requested, return it even if it's inactive '''
        return self.all_with_inactive().get(*args, **kwargs)

    def filter(self, *args, **kwargs):
        ''' if pk was specified as a kwarg, return even if it's inactive '''
        if 'pk' in kwargs:
            return self.all_with_inactive().filter(*args, **kwargs)
        return self.get_queryset().filter(*args, **kwargs)


class RawImageManager(SoftDeleteManager):
    def by_ids_or_params(self, ids, params):
        qs = super(RawImageManager, self).get_queryset()
        ids = ids.split(',') if ids else None
        if ids:
            qs = qs.filter(id__in=ids)
        else:
            factory = FOLDER_TYPE_LOOKUP['none'](source=qs)
            qs = factory.filter(params)

        return qs
