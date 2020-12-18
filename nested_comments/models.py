# Django
from django.contrib.auth.models import User

from toggleproperties.models import ToggleProperty

try:
    # Django < 1.10
    from django.contrib.contenttypes.generic import GenericForeignKey
except ImportError:
    # Django >= 1.10
    from django.contrib.contenttypes.fields import GenericForeignKey

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models


def get_sentinel_user():
    return User.objects.get_or_create(username='deleted')[0]


class NestedComment(models.Model):
    content_type = models.ForeignKey(
        ContentType,
    )

    object_id = models.PositiveIntegerField()

    content_object = GenericForeignKey(
        'content_type',
        'object_id',
    )

    author = models.ForeignKey(
        User,
        on_delete = models.SET(get_sentinel_user),
        editable = False,
    )

    text = models.TextField()

    created = models.DateTimeField(
        auto_now_add = True,
        editable = False,
    )

    updated = models.DateTimeField(
        auto_now = True,
        editable = False,
    )

    parent = models.ForeignKey(
        'self',
        null = True,
        blank = True,
        related_name = 'children',
        on_delete = models.SET_NULL,
    )

    deleted = models.BooleanField(
        default = False,
    )

    @property
    def depth(self):
        value = 1
        if self.parent:
            return value + self.parent.depth
        return value

    @property
    def likes(self):
        return ToggleProperty.objects.filter(
            object_id=self.pk,
            content_type=ContentType.objects.get_for_model(NestedComment),
            property_type='like'
        ).values_list('user__pk', flat=True)

    def __unicode__(self):
        return "Comment %d" % self.pk

    def get_absolute_url(self):
        object_url = self.content_type.get_object_for_this_type(id = self.object_id).get_absolute_url()
        return '%s#c%d' % (object_url, self.id)

    def delete(self, *args, **kwargs):
        if not self.deleted:
            self.deleted = True
            self.save()

    def clean(self, *args, **kwargs):
        obj = self.content_type.get_object_for_this_type(pk = self.object_id)
        if hasattr(obj, 'allow_comments') and obj.allow_comments is False:
            raise ValidationError('Comments are closed')

    class Meta:
        app_label = 'nested_comments'
