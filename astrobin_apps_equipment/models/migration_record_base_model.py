from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from safedelete.models import SafeDeleteModel


class MigrationRecordBaseModel(SafeDeleteModel):
    image = models.ForeignKey(
        'astrobin.Image',
        editable=False,
        on_delete=models.CASCADE,
        related_name='%(class)ss',
    )

    to_item_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    to_item_object_id = models.TextField(null=True, blank=True)
    to_item_content_object = GenericForeignKey('to_item_content_type', 'to_item_object_id')

    created = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        abstract = True
