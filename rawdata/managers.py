from django.db import models

class SoftDeleteManager(models.Manager):
    def get_query_set(self):
        return super(SoftDeleteManager, self).get_query_set().filter(active = True)

    def all_with_inactive(self):
        return super(SoftDeleteManager, self).get_query_set()

    def get(self, *args, **kwargs):
        ''' if a specific record was requested, return it even if it's inactive '''
        return self.all_with_inactive().get(*args, **kwargs)
 
    def filter(self, *args, **kwargs):
        ''' if pk was specified as a kwarg, return even if it's inactive '''
        if 'pk' in kwargs:
            return self.all_with_inactive().filter(*args, **kwargs)
        return self.get_query_set().filter(*args, **kwargs)
