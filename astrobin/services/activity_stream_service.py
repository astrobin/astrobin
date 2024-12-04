import logging

from actstream.models import Action
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db.models import Q, QuerySet

from astrobin.enums.moderator_decision import ModeratorDecision
from astrobin.models import Image, ImageRevision
from toggleproperties.models import ToggleProperty

log = logging.getLogger(__name__)


class ActivityStreamService:
    user: User
    
    def __init__(self, user):
        self.user = user

    def get_global_stream(self) -> QuerySet:
        return Action.objects.all().prefetch_related(
            'actor__userprofile',
            'actor_content_type',
            'target_content_type',
            'target'
        )

    def get_personal_stream(self) -> QuerySet:
        image_ct = ContentType.objects.get_for_model(Image)
        image_rev_ct = ContentType.objects.get_for_model(ImageRevision)
        user_ct = ContentType.objects.get_for_model(User)

        cache_key = 'astrobin_users_image_ids_%s' % self.user
        users_image_ids = cache.get(cache_key)
        if users_image_ids is None:
            users_image_ids = [
                str(x) for x in
                Image.objects.filter(user=self.user).values_list('id', flat=True)
            ]
            cache.set(cache_key, users_image_ids, 300)

        cache_key = 'astrobin_users_revision_ids_%s' % self.user
        users_revision_ids = cache.get(cache_key)
        if users_revision_ids is None:
            users_revision_ids = [
                str(x) for x in
                ImageRevision.objects.filter(image__user=self.user).values_list('id', flat=True)
            ]
            cache.set(cache_key, users_revision_ids, 300)

        cache_key = 'astrobin_followed_user_ids_%s' % self.user
        followed_user_ids = cache.get(cache_key)
        if followed_user_ids is None:
            followed_user_ids = [
                str(x) for x in
                ToggleProperty.objects.filter(
                    property_type="follow",
                    user=self.user,
                    content_type=user_ct
                ).values_list('object_id', flat=True)
            ]
            cache.set(cache_key, followed_user_ids, 900)

        cache_key = 'astrobin_followees_image_ids_%s' % self.user
        followees_image_ids = cache.get(cache_key)
        if followees_image_ids is None:
            followees_image_ids = [
                str(x) for x in
                Image.objects.filter(user_id__in=followed_user_ids).values_list('id', flat=True)
            ]
            cache.set(cache_key, followees_image_ids, 900)

        return Action.objects.prefetch_related(
            'actor__userprofile',
            'actor_content_type',
            'target_content_type',
            'target'
        ).filter(
            # Actor is user, or...
            Q(
                Q(actor_content_type=user_ct) &
                Q(actor_object_id=self.user.id)
            ) |

            # Action concerns user's images as target, or...
            Q(
                Q(target_content_type=image_ct) &
                Q(target_object_id__in=users_image_ids)
            ) |
            Q(
                Q(target_content_type=image_rev_ct) &
                Q(target_object_id__in=users_revision_ids)
            ) |

            # Action concerns user's images as object, or...
            Q(
                Q(action_object_content_type=image_ct) &
                Q(action_object_object_id__in=users_image_ids)
            ) |
            Q(
                Q(action_object_content_type=image_rev_ct) &
                Q(action_object_object_id__in=users_revision_ids)
            ) |

            # Actor is somebody the user follows, or...
            Q(
                Q(actor_content_type=user_ct) &
                Q(actor_object_id__in=followed_user_ids)
            ) |

            # Action concerns an image by a followed user...
            Q(
                Q(target_content_type=image_ct) &
                Q(target_object_id__in=followees_image_ids)
            ) |
            Q(
                Q(action_object_content_type=image_ct) &
                Q(action_object_object_id__in=followees_image_ids)
            )
        )

    def get_recent_images(self) -> QuerySet:
        return Image.objects.filter(
            Q(moderator_decision=ModeratorDecision.APPROVED) &
            Q(published__isnull=False)
        ).order_by('-published')

    def get_recent_followed_images(self) -> QuerySet:
        followed = [x.object_id for x in ToggleProperty.objects.filter(
            property_type="follow",
            content_type=ContentType.objects.get_for_model(User),
            user=self.user
        )]

        return self.get_recent_images().filter(user__in=followed)
