# Python
import datetime

# Django
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse as reverse_url
from django.db.models.signals import (
        pre_save, post_save, pre_delete, post_delete, m2m_changed)

# Third party apps
from pybb.models import Forum, Post
from rest_framework.authtoken.models import Token
from toggleproperties.models import ToggleProperty
from subscription.models import UserSubscription
from subscription.signals import subscribed, paid

# Other AstroBin apps
from nested_comments.models import NestedComment
from rawdata.models import (
    PrivateSharedFolder,
    PublicDataPool,
    RawImage,
    TemporaryArchive,
)

from astrobin_apps_groups.models import Group
from astrobin_apps_platesolving.models import Solution
from astrobin_apps_platesolving.solver import Solver
from astrobin_apps_notifications.utils import push_notification
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import (
    is_free, is_lite, is_premium)

# This app
from .models import Image, ImageRevision, Gear, UserProfile
from .gear import get_correct_gear
from .stories import add_story


def image_pre_save(sender, instance, **kwargs):
    try:
        image = sender.objects.get(pk = instance.pk)
    except sender.DoesNotExist:
        pass
    else:
        if image.moderator_decision != 1 and instance.moderator_decision == 1:
            # This image is being approved
            if not instance.is_wip:
                add_story(instance.user, verb = 'VERB_UPLOADED_IMAGE', action_object = instance)
pre_save.connect(image_pre_save, sender = Image)


def image_post_save(sender, instance, created, **kwargs):
    groups = instance.user.joined_group_set.filter(autosubmission = True)
    for group in groups:
        if instance.is_wip:
            group.images.remove(instance)
        else:
            group.images.add(instance)

    if created:
        user_scores_index = instance.user.userprofile.get_scores()['user_scores_index']
        if user_scores_index >= 1.00 or is_lite(instance.user) or is_premium(instance.user):
            instance.moderated_when = datetime.date.today()
            instance.moderator_decision = 1
            instance.save()

        instance.user.userprofile.premium_counter += 1
        instance.user.userprofile.save()

        if not instance.is_wip:
            followers = [x.user for x in ToggleProperty.objects.filter(
                property_type = "follow",
                content_type = ContentType.objects.get_for_model(User),
                object_id = instance.user.pk)]

            push_notification(followers, 'new_image',
                {
                    'object_url': settings.ASTROBIN_BASE_URL + instance.get_absolute_url(),
                    'originator': instance.user.userprofile,
                })

            if instance.moderator_decision == 1:
                add_story(instance.user, verb = 'VERB_UPLOADED_IMAGE', action_object = instance)
post_save.connect(image_post_save, sender = Image)


def image_pre_delete(sender, instance, **kwargs):
    def decrease_counter(user):
        user.userprofile.premium_counter -= 1
        user.userprofile.save()

    if is_free(instance.user):
        decrease_counter(instance.user)

    if is_lite(instance.user):
        usersub = UserSubscription.active_objects.get(
            user = instance.user,
            subscription__name = 'AstroBin Lite')

        usersub_created = usersub.expires - datetime.timedelta(365) # leap years be damned
        dt = instance.uploaded.date() - usersub_created
        if dt.days >= 0:
            decrease_counter(instance.user)


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

        add_story(instance.image.user,
                  verb = 'VERB_UPLOADED_REVISION',
                  action_object = instance,
                  target = instance.image)
post_save.connect(imagerevision_post_save, sender = ImageRevision)


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

            add_story(instance.author,
                     verb = 'VERB_COMMENTED_IMAGE',
                     action_object = instance,
                     target = obj)

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
                })

            add_story(instance.author,
                     verb = 'VERB_COMMENTED_GEAR',
                     action_object = instance,
                     target = gear)
post_save.connect(nested_comment_post_save, sender = NestedComment)


def toggleproperty_post_save(sender, instance, created, **kwargs):
    if created:
        if instance.property_type in ("like", "bookmark"):
            if instance.property_type == "like":
                verb = 'VERB_LIKED_IMAGE'
            elif instance.property_type == "bookmark":
                verb = 'VERB_BOOKMARKED_IMAGE'

            if instance.content_type == ContentType.objects.get_for_model(Image):
                image = instance.content_type.get_object_for_this_type(id = instance.object_id)
                if image.is_wip:
                    return

            add_story(instance.user,
                     verb = verb,
                     action_object = instance.content_object)

            if instance.content_type == ContentType.objects.get_for_model(Image):
                push_notification(
                    [instance.content_object.user], 'new_' + instance.property_type,
                    {
                        'url': settings.ASTROBIN_BASE_URL + instance.content_object.get_absolute_url(),
                        'title': instance.content_object.title,
                        'user': instance.user.userprofile,
                    })

        elif instance.property_type == "follow":
            user_ct = ContentType.objects.get_for_model(User)
            if instance.content_type == user_ct:
                followed_user = user_ct.get_object_for_this_type(pk = instance.object_id)
                push_notification([followed_user], 'new_follower',
                                  {'object': instance.user.userprofile,
                                   'object_url': instance.user.get_absolute_url()})
post_save.connect(toggleproperty_post_save, sender = ToggleProperty)


def rawdata_publicdatapool_post_save(sender, instance, created, **kwargs):
    if created:
        add_story(instance.creator,
                 verb = 'VERB_CREATED_DATA_POOL',
                 action_object = instance)
post_save.connect(rawdata_publicdatapool_post_save, sender = PublicDataPool)


def create_auth_token(sender, instance, created, **kwargs):
    if created:
        Token.objects.get_or_create(user = instance)
post_save.connect(create_auth_token, sender = User)


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

        add_story(instance.creator,
                 verb = 'VERB_ADDED_DATA_TO_DATA_POOL',
                 action_object = instance.images.all()[0],
                 target = instance)
m2m_changed.connect(rawdata_publicdatapool_data_added, sender = PublicDataPool.images.through)


def rawdata_publicdatapool_image_added(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action == 'post_add' and len(pk_set) > 0:
        contributors = [i.user for i in instance.images.all()]
        users = [instance.creator] + contributors
        image = Image.objects.get(pk = list(pk_set)[0])
        submitter = image.user
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

        add_story(submitter,
                 verb = 'VERB_ADDED_IMAGE_TO_DATA_POOL',
                 action_object = image,
                 target = instance)
m2m_changed.connect(rawdata_publicdatapool_image_added, sender = PublicDataPool.processed_images.through)


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
m2m_changed.connect(rawdata_privatesharedfolder_data_added, sender = PrivateSharedFolder.images.through)


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
m2m_changed.connect(rawdata_privatesharedfolder_image_added, sender = PrivateSharedFolder.processed_images.through)


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
m2m_changed.connect(rawdata_privatesharedfolder_user_added, sender = PrivateSharedFolder.users.through)


def solution_post_save(sender, instance, created, **kwargs):
    notification = None
    user = None

    ct = instance.content_type

    try:
        target = ct.get_object_for_this_type(pk = instance.object_id)
    except ct.model_class().DoesNotExist:
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
post_save.connect(solution_post_save, sender = Solution)


def subscription_subscribed(sender, **kwargs):
    subscription = kwargs.get("subscription")

    if subscription.name == 'AstroBin Lite':
        user = kwargs.get("user")
        profile = user.userprofile
        profile.premium_counter = 0
        profile.save()
subscribed.connect(subscription_subscribed)
paid.connect(subscription_subscribed)


pre_delete.connect(image_pre_delete, sender = Image)

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
                'url': settings.ASTROBIN_BASE_URL + reverse_url('group_detail', args = (instance.pk,)),
            })

        add_story(
            instance.creator,
            verb = 'VERB_CREATED_PUBLIC_GROUP',
            action_object = instance)
post_save.connect(group_post_save, sender = Group)


def group_members_changed(sender, instance, **kwargs):
    action = kwargs['action']

    if action == 'post_add':
        instance.save() # trigger date_updated update
        if instance.public:
            for pk in kwargs['pk_set']:
                user = User.objects.get(pk = pk)
                if user != instance.owner:
                    followers = [
                        x.user for x in
                        ToggleProperty.objects.toggleproperties_for_object("follow", user)
                    ]
                    push_notification(followers, 'user_joined_public_group',
                        {
                            'user': user.userprofile.get_display_name(),
                            'group_name': instance.name,
                            'url': settings.ASTROBIN_BASE_URL + reverse_url('group_detail', args = (instance.pk,)),
                        })

                    add_story(
                        user,
                        verb = 'VERB_JOINED_GROUP',
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


def forum_post_post_save(sender, instance, created, **kwargs):
    if created and hasattr(instance.topic.forum, "group"):
        instance.topic.forum.group.save() # trigger date_updated update
post_save.connect(forum_post_post_save, sender = Post)
