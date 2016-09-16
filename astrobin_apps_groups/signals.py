# Django
from django.conf import settings
from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib.auth.models import User
from django.db.models.signals import (
    m2m_changed, post_delete, pre_save, post_save)

# Third party
from actstream import action as act
from pybb.models import Forum, Post

# AstroBin
from astrobin.models import Image
from astrobin_apps_notifications.utils import push_notification
from toggleproperties.models import ToggleProperty

# This app
from astrobin_apps_groups.models import Group

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

        # Group was renamed
        if group.name != instance.name:
            group.forum.name = instance.name
            group.forum.save()

pre_save.connect(group_pre_save, sender = Group)


def group_post_save(sender, instance, created, **kwargs):
    if created and instance.creator is not None:
        instance.members.add(instance.creator)
        if instance.moderated:
            instance.moderators.add(instance.creator)

        followers = [
            x.user for x in
            ToggleProperty.objects.toggleproperties_for_object(
                "follow", User.objects.get(pk = instance.creator.pk))
        ]
        push_notification(followers, 'new_public_group_created',
            {
                'creator': instance.creator.userprofile.get_display_name(),
                'group_name': instance.name,
                'url': settings.ASTROBIN_BASE_URL + reverse('group_detail', args = (instance.pk,)),
            })

        act.send(
            instance.creator,
            verb = "created a new public group",
            action_object = instance)
post_save.connect(group_post_save, sender = Group)


def group_members_changed(sender, instance, **kwargs):
    action = kwargs['action']

    if action == 'post_add':
        instance.save() # trigger date_updated update
        if instance.public:
            for pk in kwargs['pk_set']:
                user = User.objects.get(pk = pk)
                followers = [
                    x.user for x in
                    ToggleProperty.objects.toggleproperties_for_object("follow", user)
                ]
                push_notification(followers, 'user_joined_public_group',
                    {
                        'user': user.userprofile.get_display_name(),
                        'group_name': instance.name,
                        'url': settings.ASTROBIN_BASE_URL + reverse('group_detail', args = (instance.pk,)),
                    })

                act.send(
                    user,
                    verb = "joined the public group",
                    action_object = instance)

        if instance.autosubmission:
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

def group_images_changed(sender, instance, **kwargs):
    if kwargs['action'] == 'post_add':
        if not instance.autosubmission:
            instance.save() # trigger date_updated update
m2m_changed.connect(group_images_changed, sender = Group.images.through)

def group_post_delete(sender, instance, **kwargs):
    try:
        instance.forum.delete()
    except Forum.DoesNotExist:
        pass
post_delete.connect(group_post_delete, sender = Group)

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

def forum_post_post_save(sender, instance, created, **kwargs):
    if created and instance.topic.forum.group is not None:
        instance.topic.forum.group.save() # trigger date_updated update
post_save.connect(forum_post_post_save, sender = Post)
