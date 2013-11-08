# Django
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse as reverse_url
from django.db.models.signals import m2m_changed
from django.db.models.signals import post_save

# Third party apps
from actstream import action as act
from rest_framework.authtoken.models import Token
from toggleproperties.models import ToggleProperty

# Other AstroBin apps
from nested_comments.models import NestedComment
from rawdata.models import (
    PrivateSharedFolder,
    PublicDataPool,
    RawImage,
    TemporaryArchive,
)

from astrobin_apps_platesolving.models import Solution
from astrobin_apps_platesolving.solver import Solver

# This app
from .notifications import push_notification
from .models import Image, ImageRevision, Gear, UserProfile
from .gear import get_correct_gear


def image_post_save(sender, instance, created, **kwargs):
    if created and not instance.is_wip:
        followers = [x.user for x in ToggleProperty.objects.filter(
            property_type = "follow",
            content_type = ContentType.objects.get_for_model(User),
            object_id = instance.user.pk)]

        push_notification(followers, 'new_image',
            {
                'object_url': settings.ASTROBIN_BASE_URL + instance.get_absolute_url(),
                'originator': instance.user.userprofile,
            })


def imagerevision_post_save(sender, instance, created, **kwargs):
    if created and not instance.image.is_wip:
        followers = [x.user for x in ToggleProperty.objects.filter(
            property_type = "follow",
            content_type = ContentType.objects.get_for_model(User),
            object_id = instance.user.pk)]

        push_notification(followers, 'new_image_revision',
            {
                'object_url': settings.ASTROBIN_BASE_URL + instance.get_absolute_url(),
                'originator': instance.user.userprofile,
            })


def nested_comment_post_save(sender, instance, created, **kwargs):
    if created:
        model_class = instance.content_type.model_class()
        obj = instance.content_type.get_object_for_this_type(id = instance.object_id)
        url = "http://astrobin.com/" + instance.get_absolute_url()

        if model_class == Image:
            image = instance.content_type.get_object_for_this_type(id = instance.object_id)
            if image.is_wip:
                return

            if instance.author != obj.user:
                push_notification(
                    [obj.user], 'new_comment',
                    {
                        'url': url,
                        'user': instance.author,
                    }
                )

            if instance.parent and instance.parent.author != instance.author:
                push_notification(
                    [instance.parent.author], 'new_comment_reply',
                    {
                        'url': url,
                        'user': instance.author,
                    }
                )

            verb = "commented on image"
            act.send(instance.author, verb = verb, action_object = instance, target = obj)

        elif model_class == Gear:
            if not instance.parent:
                gear, gear_type = get_correct_gear(obj.id)
                user_attr_lookup = {
                    'Telescope': 'telescopes',
                    'Camera': 'cameras',
                    'Mount': 'mounts',
                    'FocalReducer': 'focal_reducers',
                    'Software': 'software',
                    'Filter': 'filters',
                    'Accessory': 'accessories',
                }

                recipients = [x.user for x in UserProfile.objects.filter(
                    **{user_attr_lookup[gear_type]: gear})]
                notification = 'new_gear_discussion'
            else:
                notification = 'new_comment_reply'
                recipients = [instance.parent.author]

            push_notification(
                recipients, notification,
                {
                    'url': url,
                    'user': instance.author,
                }
            )

            verb = "commented on gear"
            act.send(instance.author, verb = verb, action_object = instance, target = gear)


def toggleproperty_post_save(sender, instance, created, **kwargs):
    if created:
        if instance.property_type in ("like", "bookmark"):
            if instance.property_type == "like":
                verb = "likes"
            elif instance.property_type == "bookmark":
                verb = "bookmarked"

            if instance.content_type == ContentType.objects.get_for_model(Image):
                image = instance.content_type.get_object_for_this_type(id = instance.object_id)
                if image.is_wip:
                    return

            act.send(instance.user, verb = verb, target = instance.content_object)

            if instance.content_type == ContentType.objects.get_for_model(Image):
                push_notification(
                    [instance.content_object.user], 'new_' + instance.property_type,
                    {
                        'url': settings.ASTROBIN_BASE_URL + instance.content_object.get_absolute_url(),
                        'user': instance.user.userprofile,
                    })

        elif instance.property_type == "follow":
            user_ct = ContentType.objects.get_for_model(User)
            if instance.content_type == user_ct:
                followed_user = user_ct.get_object_for_this_type(pk = instance.object_id)
                push_notification([followed_user], 'new_follower',
                                  {'object': instance.user.userprofile,
                                   'object_url': instance.user.get_absolute_url()})



def rawdata_publicdatapool_post_save(sender, instance, created, **kwargs):
    verb = "created a new public data pool"
    if created:
        act.send(instance.creator, verb = verb, target = instance)


def create_auth_token(sender, instance, created, **kwargs):
    if created:
        Token.objects.get_or_create(user = instance)


def rawdata_publicdatapool_data_added(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action == 'post_add' and len(pk_set) > 0:
        contributors = [i.user for i in instance.images.all()]
        users = [instance.creator] + contributors
        submitter = RawImage.objects.get(pk = list(pk_set)[0]).user
        users[:] = [x for x in users if x != submitter]
        push_notification(
            users,
            'rawdata_posted_to_pool',
            {
                'user_name': submitter.username,
                'user_url': reverse_url('user_page', kwargs = {'username': submitter.username}),
                'pool_name': instance.name,
                'pool_url': reverse_url('rawdata.publicdatapool_detail', kwargs = {'pk': instance.pk}),
            },
        )

        verb = "added new data to public data pool"
        act.send(instance.creator, verb = verb, target = instance)


def rawdata_publicdatapool_image_added(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action == 'post_add' and len(pk_set) > 0:
        contributors = [i.user for i in instance.images.all()]
        users = [instance.creator] + contributors
        submitter = Image.objects.get(pk = list(pk_set)[0]).user
        users[:] = [x for x in users if x != submitter]
        push_notification(
            users,
            'rawdata_posted_image_to_public_pool',
            {
                'user_name': submitter.username,
                'user_url': reverse_url('user_page', kwargs = {'username': submitter.username}),
                'pool_name': instance.name,
                'pool_url': reverse_url('rawdata.publicdatapool_detail', kwargs = {'pk': instance.pk}),
            },
        )

        verb = "added a new processed image to public data pool"
        act.send(instance.creator, verb = verb, target = instance)


def rawdata_privatesharedfolder_data_added(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action == 'post_add' and len(pk_set) > 0:
        invitees = instance.users.all()
        users = [instance.creator] + list(invitees)
        submitter = RawImage.objects.get(pk = list(pk_set)[0]).user
        users[:] = [x for x in users if x != submitter]
        push_notification(
            users,
            'rawdata_posted_to_private_folder',
            {
                'user_name': submitter.username,
                'user_url': reverse_url('user_page', kwargs = {'username': submitter.username}),
                'folder_name': instance.name,
                'folder_url': reverse_url('rawdata.privatesharedfolder_detail', kwargs = {'pk': instance.pk}),
            },
        )


def rawdata_privatesharedfolder_image_added(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action == 'post_add' and len(pk_set) > 0:
        invitees = instance.users.all()
        users = [instance.creator] + list(invitees)
        submitter = Image.objects.get(pk = list(pk_set)[0]).user
        users[:] = [x for x in users if x != submitter]
        push_notification(
            users,
            'rawdata_posted_image_to_private_folder',
            {
                'user_name': submitter.username,
                'user_url': reverse_url('user_page', kwargs = {'username': submitter.username}),
                'folder_name': instance.name,
                'folder_url': reverse_url('rawdata.privatesharedfolder_detail', kwargs = {'pk': instance.pk}),
            },
        )


def rawdata_privatesharedfolder_user_added(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action == 'post_add' and len(pk_set) > 0:
        user = User.objects.get(pk = list(pk_set)[0])
        push_notification(
            [user],
            'rawdata_invited_to_private_folder',
            {
                'folder_name': instance.name,
                'folder_url': reverse_url('rawdata.privatesharedfolder_detail', kwargs = {'pk': instance.pk}),
            },
        )


def solution_post_save(sender, instance, created, **kwargs):
    notification = None
    user = None

    ct = instance.content_type

    try:
        target = ct.get_object_for_this_type(pk = instance.object_id)
    except ct.get_model().DoesNotExist:
        return

    if ct.model == 'image':
        user = target.user
    elif ct.model == 'imagerevision':
        user = target.image.user
    else:
        return

    if instance.status == Solver.FAILED:
        notification = 'image_not_solved'
    elif instance.status == Solver.SUCCESS:
        notification = 'image_solved'
    else:
        return

    push_notification([user], notification,
        {'object_url': settings.ASTROBIN_BASE_URL + target.get_absolute_url()})


post_save.connect(image_post_save, sender = Image)
post_save.connect(imagerevision_post_save, sender = ImageRevision)
post_save.connect(nested_comment_post_save, sender = NestedComment)
post_save.connect(toggleproperty_post_save, sender = ToggleProperty)
post_save.connect(rawdata_publicdatapool_post_save, sender = PublicDataPool)
post_save.connect(solution_post_save, sender = Solution)
post_save.connect(create_auth_token, sender = User)

m2m_changed.connect(rawdata_publicdatapool_data_added, sender = PublicDataPool.images.through)
m2m_changed.connect(rawdata_publicdatapool_image_added, sender = PublicDataPool.processed_images.through)
m2m_changed.connect(rawdata_privatesharedfolder_data_added, sender = PrivateSharedFolder.images.through)
m2m_changed.connect(rawdata_privatesharedfolder_image_added, sender = PrivateSharedFolder.processed_images.through)
m2m_changed.connect(rawdata_privatesharedfolder_user_added, sender = PrivateSharedFolder.users.through)


