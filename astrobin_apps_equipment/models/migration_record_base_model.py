from django.db import models
from safedelete.models import SafeDeleteModel


class MigrationRecordBaseModel(SafeDeleteModel):
    image = models.ForeignKey(
        'astrobin.Image',
        editable=False,
        on_delete=models.CASCADE,
        related_name='%(class)ss',
    )

    created = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        abstract = True
