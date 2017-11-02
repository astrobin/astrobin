from django.db.models import ObjectDoesNotExist

from rest_framework import serializers


# See: https://groups.google.com/forum/?fromgroups=#!topic/django-rest-framework/gYGaFko27Vk
class PKRelatedFieldAcceptNull(serializers.PrimaryKeyRelatedField):
    # overwrite from native to change the logic for handling object lookups that return nothing
    def from_native(self, data):
        if self.queryset is None:
            raise Exception('Writable related fields must include a `queryset` argument')
        try:
            # if no object is found, then set the value to "None" instead of raising exception
            return self.queryset.get(pk=data)
        except ObjectDoesNotExist:
            return None
