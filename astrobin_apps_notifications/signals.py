from django.apps import apps
from django.db.models.signals import post_migrate

from notification import models as notification

from .types import NOTICE_TYPES


def create_notice_types(sender, **kwargs):
    for notice_type in NOTICE_TYPES:
        notification.create_notice_type(notice_type[0],
                                        notice_type[1],
                                        notice_type[2],
                                        default = notice_type[3])

astrobin = apps.get_app_config('astrobin')
post_migrate.connect(create_notice_types, sender=astrobin)
