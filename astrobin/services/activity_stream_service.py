import logging

from actstream.models import Action
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
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
        return Action.objects.user(self.user).prefetch_related(
            'actor__userprofile',
            'actor_content_type',
            'target_content_type',
            'target'
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
