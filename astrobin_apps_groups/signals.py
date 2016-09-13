# Django
from django.db.models.signals import (
    m2m_changed, post_delete, pre_save, post_save)

# Third party
from pybb.models import Forum

# AstroBin
from astrobin.models import Image

# This app
from astrobin_apps_groups.models import Group


def group_post_delete(sender, instance, **kwargs):
    try:
        instance.forum.delete()
    except Forum.DoesNotExist:
        pass
post_delete.connect(group_post_delete, sender = Group)


# Keep images in sync when group is autosubmission
def group_pre_save(sender, instance, **kwargs):
    try:
        group = sender.objects.get(pk = instance.pk)
    except sender.DoesNotExist:
        pass
    else:
        # Group is becoming autosubmission
        if not group.autosubmission and instance.autosubmission:
            instance.images.clear()
            images = Image.all_objects.filter(user__in = instance.members.all())
            for image in images:
                instance.images.add(image)
pre_save.connect(group_pre_save, sender = Group)


def group_members_changed(sender, instance, **kwargs):
    action = kwargs['action']

    if action == 'post_add' and instance.autosubmission:
        images = Image.all_objects.filter(user__pk__in = kwargs['pk_set'])
        for image in images:
            instance.images.add(image)
    elif action == 'post_remove':
        images = Image.all_objects.filter(user__pk__in = kwargs['pk_set'])
        for image in images:
            instance.images.remove(image)
    elif action == 'post_clear':
        instance.images.clear()
m2m_changed.connect(group_members_changed, sender = Group.members.through)


def image_post_save(sender, instance, created, **kwargs):
    groups = instance.user.joined_group_set.filter(autosubmission = True)
    if instance.is_wip:
        for group in groups:
            group.images.remove(instance)
    else:
        groups = instance.user.joined_group_set.filter(autosubmission = True)
        for group in groups:
            group.images.add(instance)
post_save.connect(image_post_save, sender = Image)
