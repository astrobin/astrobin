from django.db import models


class PlateSolvingAdvancedTask(models.Model):
    PRIORITY_CHOICES = (
        ('normal', 'Normal'),
        ('low', 'Low'),
    )

    serial_number = models.CharField(
        max_length=32,
        null=False,
        blank=False,
    )

    created = models.DateTimeField(
        auto_now_add=True
    )

    active = models.BooleanField(
        default=True,
    )

    task_params = models.TextField(
        null=False,
        blank=False,
    )

    status = models.CharField(
        max_length=8,
        null=True,
        editable=False,
        choices=(("OK", "OK"), ("ERROR", "ERROR")),
    )

    error_message = models.CharField(
        max_length=512,
        null=True,
        editable=False,
    )
    
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='normal',
        db_index=True,
    )
