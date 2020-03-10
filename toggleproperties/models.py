from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.dispatch import receiver

try:
    from django.contrib.contenttypes.generic import GenericForeignKey
except ImportError:
    from django.contrib.contenttypes.fields import GenericForeignKey


class TogglePropertyManager(models.Manager):
    def toggleproperties_for_user(self, property_type, user):
        return self.get_queryset().filter(user=user, property_type=property_type)

    def toggleproperties_for_model(self, property_type, model, user=None):
        content_type = ContentType.objects.get_for_model(model)
        qs = self.get_queryset().filter(content_type=content_type, property_type=property_type)
        if user:
            qs = qs.filter(user=user)
        return qs

    def toggleproperties_for_object(self, property_type, obj, user=None):
        content_type = ContentType.objects.get_for_model(type(obj))
        qs = self.get_queryset().filter(content_type=content_type,
                                        property_type=property_type,
                                        object_id=obj.pk)
        if user:
            qs = qs.filter(user=user)

        return qs

    def toggleproperties_for_objects(self, property_type, object_list, user=None):
        object_ids = [o.pk for o in object_list]
        if not object_ids:
            return {}

        content_type = ContentType.objects.get_for_model(object_list[0])

        qs = self.get_queryset().filter(content_type=content_type,
                                        property_type=property_type,
                                        object_id__in=object_ids)
        counters = qs.values('object_id').annotate(count=models.Count('object_id'))
        results = {}
        for c in counters:
            results.setdefault(c['object_id'], {})['count'] = c['count']
            results.setdefault(c['object_id'], {})['is_toggled'] = False
            results.setdefault(c['object_id'], {})['content_type_id'] = content_type.id
        if user and user.is_authenticated():
            qs = qs.filter(user=user)
            for f in qs:
                results.setdefault(f.object_id, {})['is_toggled'] = True

        return results

    def toggleproperty_for_user(self, property_type, obj, user):
        content_type = ContentType.objects.get_for_model(type(obj))
        return self.get_queryset().get(content_type=content_type,
                                       property_type=property_type,
                                       user=user, object_id=obj.pk)

    def create_toggleproperty(self, property_type, content_object, user):
        content_type = ContentType.objects.get_for_model(type(content_object))
        try:
            tp = self.toggleproperty_for_user(property_type, content_object, user)
        except ToggleProperty.DoesNotExist:
            tp = ToggleProperty(
                user=user,
                property_type=property_type,
                content_type=content_type,
                object_id=content_object.pk,
                content_object=content_object
            )
            tp.save()

        return tp


class ToggleProperty(models.Model):
    property_type = models.CharField(max_length=64)
    user = models.ForeignKey(User)
    content_type = models.ForeignKey(ContentType)
    object_id = models.TextField()
    content_object = GenericForeignKey('content_type', 'object_id')

    created_on = models.DateTimeField(auto_now_add=True)

    objects = TogglePropertyManager()

    class Meta:
        verbose_name = "Toggle property"
        verbose_name_plural = "Toggle properties"
        unique_together = (('property_type', 'user', 'content_type', 'object_id'),)

    def __unicode__(self):
        return u"%s (%s) %s" % (self.user, self.property_type, self.content_object)


@receiver(models.signals.post_delete)
def remove_toggleproperty(sender, **kwargs):
    instance = kwargs.get('instance')
    if hasattr(instance, 'id'):
        content_type = ContentType.objects.get_for_model(ToggleProperty)
        ToggleProperty.objects.filter(content_type=content_type, object_id=instance.id).delete()
