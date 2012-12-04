# Django
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models


class NestedComment(models.Model):
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

    def __unicode__(self):
        return "%s: \"%s\"" % (self.author, self.text)

    def delete(self):
        if self.deleted == False:
            self.deleted = True;
            self.save();

    class Meta:
        app_label = 'nested_comments'

    class MPTTMeta:
        order_insertion_bu = ['created']
