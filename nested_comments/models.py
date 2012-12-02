# Django
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models

# Third party apps
from mptt.models import MPTTModel, TreeForeignKey

class NestedComment(MPTTModel):
    content_type = models.ForeignKey(
        ContentType,
    )

    object_id = models.PositiveIntegerField()

    content_object = generic.GenericForeignKey(
        'content_type',
        'object_id',
    )

    author = models.ForeignKey(
        User,
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

    parent = TreeForeignKey(
        'self',
        null = True,
        blank = True,
        editable = False,
        related_name = 'children'
    )

    deleted = models.BooleanField(
        default = False,
    )

    def __unicode__(self):
        return "%s: \"%s\"" % (self.author, self.text)

    class Meta:
        app_label = 'nested_comments'

    class MPTTMeta:
        order_insertion_bu = ['created']
