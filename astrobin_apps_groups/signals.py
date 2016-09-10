# Django
from django.db.models.signals import post_delete

# Third party
from pybb.models import Forum

# This app
from astrobin_apps_groups.models import Group


def group_post_delete(sender, instance, **kwargs):
    try:
        instance.forum.delete()
    except Forum.DoesNotExist:
        pass
post_delete.connect(group_post_delete, sender = Group)
