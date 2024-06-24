from django.db import models
from safedelete.models import SafeDeleteModel

from astrobin.utils import generate_unique_hash


class HashedSafeDeleteModel(SafeDeleteModel):
    hash = models.CharField(
        max_length=6,
        null=True,
        unique=True
    )

    def __init__(self, *args, **kwargs):
        super(HashedSafeDeleteModel, self).__init__(*args, **kwargs)
        if not self.hash:
            self.hash = generate_unique_hash(6, self.__class__.all_objects)

    class Meta:
        abstract = True
