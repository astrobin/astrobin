import datetime
from itertools import chain

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User, Group as DjangoGroup
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse as reverse_url
from django.db import IntegrityError
from django.db import transaction
from django.db.models.signals import (
    pre_save, post_save, post_delete, m2m_changed)
from django.utils.translation import ugettext_lazy as _
from gadjo.requestprovider.signals import get_request
from pybb.models import Forum, Topic, Post
from rest_framework.authtoken.models import Token
from reviews.models import Review
from safedelete.signals import post_softdelete
from subscription.models import UserSubscription, Subscription
from subscription.signals import subscribed, paid, signed_up
from threaded_messages.models import Thread

from astrobin_apps_groups.models import Group
from astrobin_apps_notifications.utils import push_notification
from astrobin_apps_platesolving.models import Solution
from astrobin_apps_platesolving.solver import Solver
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import (
    is_lite, is_any_premium_subscription, is_lite_2020, is_any_ultimate, is_premium_2020, is_premium)
from astrobin_apps_premium.utils import premium_get_valid_usersubscription
from nested_comments.models import NestedComment
from toggleproperties.models import ToggleProperty
from .gear import get_correct_gear
from .models import Image, ImageRevision, Gear, UserProfile
from .stories import add_story


def image_pre_save(sender, instance, **kwargs):
    if not instance.pk and not instance.is_wip:
        instance.published = datetime.datetime.now()

    try:
        image = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        pass
    else:
        if image.moderator_decision != 1 and instance.moderator_decision == 1:
            # This image is being approved
            if not instance.is_wip:
                add_story(instance.user, verb='VERB_UPLOADED_IMAGE', action_object=instance)

        if not instance.is_wip and not instance.published:
            instance.published = datetime.datetime.now()


pre_save.connect(image_pre_save, sender=Image)


def image_post_save(sender, instance, created, **kwargs):
    # type: (object, Image, bool, object) -> None

    profile_saved = False

    groups = instance.user.joined_group_set.filter(autosubmission=True)
    for group in groups:
        if instance.is_wip:
            group.images.remove(instance)
        else:
            group.images.add(instance)

    if created:
        user_scores_index = instance.user.userprofile.get_scores()['user_scores_index']
        if user_scores_index >= 1.00 or is_any_premium_subscription(instance.user):
            instance.moderated_when = datetime.date.today()
            instance.moderator_decision = 1
            instance.save(keep_deleted=True)

        instance.user.userprofile.premium_counter += 1
        instance.user.userprofile.save(keep_deleted=True)
        profile_saved = True

        if not instance.is_wip and not instance.skip_notifications:
            followers = [x.user for x in ToggleProperty.objects.filter(
                property_type="follow",
                content_type=ContentType.objects.get_for_model(User),
                object_id=instance.user.pk)]

            thumb = instance.thumbnail_raw('gallery', {'sync': True})
            push_notification(followers, 'new_image', {
                'image': instance,
                'image_thumbnail': thumb.url if thumb else None
            })

            if instance.moderator_decision == 1:
                add_story(instance.user, verb='VERB_UPLOADED_IMAGE', action_object=instance)

    if not profile_saved:
        # Trigger update of auto_add fields
        try:
            instance.user.userprofile.save(keep_deleted=True)
        except UserProfile.DoesNotExist:
            pass

    # Trigger real time search index
    instance.user.save()


post_save.connect(image_post_save, sender=Image)


def image_post_delete(sender, instance, **kwargs):
    def decrease_counter(user):
        user.userprofile.premium_counter -= 1
        with transaction.atomic():
            user.userprofile.save(keep_deleted=True)

    try:
        if is_lite(instance.user):
            usersub = premium_get_valid_usersubscription(instance.user)
            usersub_created = usersub.expires - relativedelta(years=1)
            dt = instance.uploaded.date() - usersub_created
            if dt.days >= 0:
                decrease_counter(instance.user)
        elif is_lite_2020(instance.user) or \
                is_premium(instance.user) or \
                is_premium_2020(instance.user) or \
                is_any_ultimate(instance.user):
            decrease_counter(instance.user)
    except IntegrityError:
        # Possibly the user is being deleted
        pass


post_softdelete.connect(image_post_delete, sender=Image)


def imagerevision_post_save(sender, instance, created, **kwargs):
    if created and not instance.image.is_wip and not instance.skip_notifications:
        followers = [x.user for x in ToggleProperty.objects.filter(
            property_type="follow",
            content_type=ContentType.objects.get_for_model(User),
            object_id=instance.image.user.pk)]

        push_notification(followers, 'new_image_revision',
                          {
                              'object_url': settings.BASE_URL + instance.get_absolute_url(),
                              'originator': instance.image.user.userprofile.get_display_name(),
                          })

        add_story(instance.image.user,
                  verb='VERB_UPLOADED_REVISION',
                  action_object=instance,
                  target=instance.image)


post_save.connect(imagerevision_post_save, sender=ImageRevision)


def nested_comment_post_save(sender, instance, created, **kwargs):
    if created:
        model_class = instance.content_type.model_class()
        obj = instance.content_type.get_object_for_this_type(id=instance.object_id)
        url = settings.BASE_URL + instance.get_absolute_url()

        if model_class == Image:
            image = instance.content_type.get_object_for_this_type(id=instance.object_id)
            if image.is_wip:
                return

            if instance.author != obj.user:
                push_notification(
                    [obj.user], 'new_comment',
                    {
                        'url': url,
                        'user': instance.author.userprofile.get_display_name(),
                        'user_url': settings.BASE_URL + reverse_url(
                            'user_page', kwargs={'username': instance.author.username}),
                    }
                )

            if instance.parent and instance.parent.author != instance.author:
                push_notification(
                    [instance.parent.author], 'new_comment_reply',
                    {
                        'url': url,
                        'user': instance.author.userprofile.get_display_name(),
                        'user_url': settings.BASE_URL + reverse_url(
                            'user_page', kwargs={'username': instance.author.username}),
                    }
                )

            add_story(instance.author,
                      verb='VERB_COMMENTED_IMAGE',
                      action_object=instance,
                      target=obj)

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
                    'user': instance.author.userprofile.get_display_name(),
                    'user_url': settings.BASE_URL + reverse_url(
                        'user_page', kwargs={'username': instance.author.username}),
                })

            add_story(instance.author,
                      verb='VERB_COMMENTED_GEAR',
                      action_object=instance,
                      target=gear)

        if hasattr(instance.content_object, "updated"):
            # This will trigger the auto_now fields in the content_object
            # We do it only if created, because the content_object needs to
            # only be updated if the number of comments changes.
            instance.content_object.save(keep_deleted=True)


post_save.connect(nested_comment_post_save, sender=NestedComment)


def toggleproperty_post_delete(sender, instance, **kwargs):
    if hasattr(instance.content_object, "updated"):
        # This will trigger the auto_now fields in the content_object
        try:
            instance.content_object.save(keep_deleted=True)
        except instance.content_object.DoesNotExist:
            pass


post_delete.connect(toggleproperty_post_delete, sender=ToggleProperty)


def toggleproperty_post_save(sender, instance, created, **kwargs):
    if hasattr(instance.content_object, "updated"):
        # This will trigger the auto_now fields in the content_object
        instance.content_object.save(keep_deleted=True)

    if created:
        if instance.property_type in ("like", "bookmark"):
            if instance.property_type == "like":
                verb = 'VERB_LIKED_IMAGE'
            elif instance.property_type == "bookmark":
                verb = 'VERB_BOOKMARKED_IMAGE'

            if instance.content_type == ContentType.objects.get_for_model(Image):
                image = instance.content_type.get_object_for_this_type(id=instance.object_id)
                if image.is_wip:
                    return

            add_story(instance.user,
                      verb=verb,
                      action_object=instance.content_object)

            if instance.content_type == ContentType.objects.get_for_model(Image):
                push_notification(
                    [instance.content_object.user], 'new_' + instance.property_type,
                    {
                        'url': settings.BASE_URL + instance.content_object.get_absolute_url(),
                        'title': instance.content_object.title,
                        'user': instance.user.userprofile.get_display_name(),
                        'user_url': settings.BASE_URL + reverse_url(
                            'user_page', kwargs={'username': instance.user.username}),
                    })

        elif instance.property_type == "follow":
            user_ct = ContentType.objects.get_for_model(User)
            if instance.content_type == user_ct:
                followed_user = user_ct.get_object_for_this_type(pk=instance.object_id)
                push_notification(
                    [followed_user], 'new_follower', {
                        'object': instance.user.userprofile.get_display_name(),
                        'object_url': settings.BASE_URL + reverse_url(
                            'user_page', kwargs={'username': instance.user.username}),
                    }
                )


post_save.connect(toggleproperty_post_save, sender=ToggleProperty)


def create_auth_token(sender, instance, created, **kwargs):
    if created:
        Token.objects.get_or_create(user=instance)


post_save.connect(create_auth_token, sender=User)


def solution_post_save(sender, instance, created, **kwargs):
    ct = instance.content_type

    try:
        target = ct.get_object_for_this_type(pk=instance.object_id)
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
                      {'object_url': settings.BASE_URL + target.get_absolute_url()})


post_save.connect(solution_post_save, sender=Solution)


def subscription_subscribed(sender, **kwargs):
    subscription = kwargs.get("subscription")

    if subscription.group.name in [
        'astrobin_lite', 'astrobin_premium',
        'astrobin_lite_2020', 'astrobin_premium_2020',
        'astrobin_ultimate_2020'
    ] and subscription.recurrence_unit is None:
        usersubscription = kwargs.get("usersubscription")
        # AstroBin Premium/Lite/Ultimate are valid for 1 year
        usersubscription.expires = datetime.datetime.now()
        usersubscription.extend(datetime.timedelta(days=365.2425))
        usersubscription.save()

        # Invalidate other premium subscriptions
        UserSubscription.active_objects \
            .filter(user=usersubscription.user,
                    subscription__category__startswith='premium') \
            .exclude(pk=usersubscription.pk) \
            .update(active=False)

    if subscription.group.name == 'astrobin_lite':
        user = kwargs.get("user")
        profile = user.userprofile
        profile.premium_counter = 0
        profile.save(keep_deleted=True)

subscribed.connect(subscription_subscribed)
paid.connect(subscription_subscribed)
signed_up.connect(subscription_subscribed)


def reset_lite_and_premium_counter(sender, **kwargs):
    subscription = kwargs.get("subscription")  # type: Subscription
    usersubscription = kwargs.get("usersubscription")  # type: UserSubscription
    user = usersubscription.user  # type: User

    if subscription.group.name in ('astrobin_lite_2020', 'astrobin_premium_2020'):
        previous = UserSubscription.objects.filter(
            user__username=user.username,
            subscription__name__in=("AstroBin Premium", "AstroBin Lite"),
            expires__gte=datetime.date.today() - datetime.timedelta(days=180)
        )

        if previous:
            user.userprofile.premium_counter = 0
            user.userprofile.save()

signed_up.connect(reset_lite_and_premium_counter)


def group_pre_save(sender, instance, **kwargs):
    try:
        group = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        pass
    else:
        # Group is becoming autosubmission
        if not group.autosubmission and instance.autosubmission:
            instance.images.clear()
            images = Image.objects_including_wip.filter(user__in=instance.members.all())
            for image in images:
                instance.images.add(image)

        # Group was renamed
        if group.name != instance.name:
            group.forum.name = instance.name
            group.forum.save()


pre_save.connect(group_pre_save, sender=Group)


def group_post_save(sender, instance, created, **kwargs):
    if created and instance.creator is not None:
        instance.members.add(instance.creator)
        if instance.moderated:
            instance.moderators.add(instance.creator)

        if instance.public:
            followers = [
                x.user for x in
                ToggleProperty.objects.toggleproperties_for_object(
                    "follow", UserProfile.objects.get(user__pk=instance.creator.pk).user)
            ]
            push_notification(followers, 'new_public_group_created',
                              {
                                  'creator': instance.creator.userprofile.get_display_name(),
                                  'group_name': instance.name,
                                  'url': settings.BASE_URL + reverse_url('group_detail', args=(instance.pk,)),
                              })

            add_story(
                instance.creator,
                verb='VERB_CREATED_PUBLIC_GROUP',
                action_object=instance)


post_save.connect(group_post_save, sender=Group)


def group_members_changed(sender, instance, **kwargs):
    action = kwargs['action']
    pk_set = kwargs['pk_set']

    group_sync_map = {
        'IOTD Submitters': ['iotd_submitters', 'content_moderators', 'iotd_staff'],
        'IOTD Reviewers': ['iotd_reviewers', 'content_moderators', 'iotd_staff'],
        'IOTD Judges': ['iotd_judges', 'content_moderators', 'iotd_staff'],
    }
    if instance.name in group_sync_map.keys():
        for django_group in group_sync_map[instance.name]:
            DjangoGroup.objects.get_or_create(name=django_group)
        django_groups = DjangoGroup.objects.filter(name__in=group_sync_map[instance.name])
    try:
        iotd_staff_group = Group.objects.get(name='IOTD Staff')
    except Group.DoesNotExist:
        iotd_staff_group = None

    if action == 'post_add':
        users = [profile.user for profile in UserProfile.objects.filter(user__pk__in=pk_set)]
        instance.save()  # trigger date_updated update

        if instance.public:
            for pk in pk_set:
                user = UserProfile.objects.get(user__pk=pk).user
                if user != instance.owner:
                    followers = [
                        x.user for x in
                        ToggleProperty.objects.toggleproperties_for_object("follow", user)
                    ]
                    push_notification(followers, 'user_joined_public_group',
                                      {
                                          'user': user.userprofile.get_display_name(),
                                          'group_name': instance.name,
                                          'url': settings.BASE_URL + reverse_url('group_detail', args=(instance.pk,)),
                                      })

                    add_story(
                        user,
                        verb='VERB_JOINED_GROUP',
                        action_object=instance)

        if instance.autosubmission:
            images = Image.objects_including_wip.filter(user__pk__in=pk_set)
            for image in images:
                instance.images.add(image)

        # Sync IOTD AstroBin groups with django groups
        if instance.name in group_sync_map.keys():
            for django_group in django_groups:
                django_group.user_set.add(*list(users))
            if iotd_staff_group:
                for user in users:
                    iotd_staff_group.members.add(user)

    elif action == 'post_remove':
        users = [profile.user for profile in UserProfile.objects.filter(user__pk__in=pk_set)]
        images = Image.objects_including_wip.filter(user__pk__in=pk_set)
        for image in images:
            instance.images.remove(image)

        if instance.forum and not instance.public:
            topics = Topic.objects.filter(forum=instance.forum)
            for topic in topics:
                topic.subscribers.remove(*User.objects.filter(pk__in=kwargs['pk_set']))

        # Sync IOTD AstroBin groups with django groups
        if instance.name in group_sync_map.keys():
            all_members = []
            all_members_chain = chain([
                x.members.all()
                for x in Group.objects \
                    .filter(name__in=group_sync_map.keys()) \
                    .exclude(name=instance.name)
            ])
            for chain_item in all_members_chain:
                all_members += chain_item
            for user in [x for x in users if x not in all_members]:
                for django_group in django_groups:
                    django_group.user_set.remove(user)
                if iotd_staff_group:
                    iotd_staff_group.members.remove(user)

    elif action == 'pre_clear':
        # Sync IOTD AstroBin groups with django groups
        users = instance.members.all()
        if instance.name in group_sync_map.keys():
            all_members = []
            all_members_chain = chain([
                x.members.all()
                for x in Group.objects \
                    .filter(name__in=group_sync_map.keys()) \
                    .exclude(name=instance.name)
            ])
            for chain_item in all_members_chain:
                all_members += chain_item
            for user in [x for x in users if x not in all_members]:
                for django_group in django_groups:
                    django_group.user_set.remove(user)
                if iotd_staff_group:
                    iotd_staff_group.members.remove(user)

    elif action == 'post_clear':
        instance.images.clear()


m2m_changed.connect(group_members_changed, sender=Group.members.through)


def group_images_changed(sender, instance, **kwargs):
    if kwargs['action'] == 'post_add':
        if not instance.autosubmission:
            instance.save()  # trigger date_updated update


m2m_changed.connect(group_images_changed, sender=Group.images.through)


def group_post_delete(sender, instance, **kwargs):
    try:
        instance.forum.delete()
    except Forum.DoesNotExist:
        pass


post_delete.connect(group_post_delete, sender=Group)


def forum_topic_pre_save(sender, instance, **kwargs):
    if not hasattr(instance.forum, 'group'):
        return

    try:
        topic = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        pass
    else:
        if topic.on_moderation == True and instance.on_moderation == False:
            # This topic is being approved
            group = instance.forum.group
            push_notification(
                [x for x in group.members.all() if x != instance.user],
                'new_topic_in_group',
                {
                    'user': instance.user.userprofile.get_display_name(),
                    'url': settings.BASE_URL + instance.get_absolute_url(),
                    'group_url': reverse_url('group_detail', kwargs={'pk': group.pk}),
                    'group_name': group.name,
                    'topic_title': instance.name,
                },
            )


pre_save.connect(forum_topic_pre_save, sender=Topic)


def forum_topic_post_save(sender, instance, created, **kwargs):
    if created and hasattr(instance.forum, 'group'):
        group = instance.forum.group

        if instance.on_moderation:
            recipients = group.moderators.all()
        else:
            recipients = group.members.all()
        recipients = [x for x in recipients if x != instance.user]

        push_notification(
            recipients,
            'new_topic_in_group',
            {
                'user': instance.user.userprofile.get_display_name(),
                'url': settings.BASE_URL + instance.get_absolute_url(),
                'group_url': settings.BASE_URL + reverse_url('group_detail', kwargs={'pk': group.pk}),
                'group_name': group.name,
                'topic_title': instance.name,
            },
        )


post_save.connect(forum_topic_post_save, sender=Topic)


def forum_post_post_save(sender, instance, created, **kwargs):
    if created and hasattr(instance.topic.forum, "group"):
        instance.topic.forum.group.save()  # trigger date_updated update


post_save.connect(forum_post_post_save, sender=Post)


def review_post_save(sender, instance, created, **kwargs):
    verb = "VERB_WROTE_REVIEW"
    if created:
        add_story(instance.user,
                  verb=verb,
                  action_object=instance,
                  target=instance.content_object)


post_save.connect(review_post_save, sender=Review)


def threaded_messages_thread_post_save(sender, instance, created, **kwargs):
    if created:
        try:
            request = get_request()
        except InexError:
            # This may happen during unit testing
            return

        messages.success(request, _("Message sent"))


post_save.connect(threaded_messages_thread_post_save, sender=Thread)


def user_post_save(sender, instance, created, **kwargs):
    if not created:
        try:
            instance.userprofile.save(keep_deleted=True)
        except UserProfile.DoesNotExist:
            pass


post_save.connect(user_post_save, sender=User)


def userprofile_post_delete(sender, instance, **kwargs):
    # Images are attached to the auth.User oject, and that's not really
    # deleted, so nothing is cascaded, hence the following line.
    instance.user.is_active = False
    instance.user.save()
    Image.objects_including_wip.filter(user=instance.user).delete()


post_softdelete.connect(userprofile_post_delete, sender=UserProfile)
