from django.db import models


class PlateSolvingAdvancedLiveLogEntry(models.Model):
    serial_number = models.CharField(
        max_length=32,
        null=False,
        editable=False,
    )

    timestamp = models.DateTimeField(
        null=False,
        editable=False,
    )

    stage = models.CharField(
        null=False,
        editable=False,
        max_length=32,
    )

    log = models.TextField(
        null=True,
        editable=False,
    )
