from django.contrib.auth.models import User
from django.db.models import Exists, OuterRef, QuerySet

from astrobin.models import PopupMessage, PopupMessageUserStatus


class PopupMessageService:
    @staticmethod
    def get_unseen_active_popups(user: User) -> QuerySet:
        if not user.is_authenticated:
            return PopupMessage.objects.none()

        # Get IDs of all active popup messages
        active_popup_ids = set(PopupMessage.objects.filter(active=True).values_list('id', flat=True))

        # Get IDs of all popups the user has seen
        seen_popup_ids = set(PopupMessageUserStatus.objects.filter(
            user=user,
            popup_message__in=active_popup_ids
        ).values_list('popup_message_id', flat=True))

        # Find IDs of active popups that the user hasn't seen
        unseen_popup_ids = active_popup_ids - seen_popup_ids

        # Get all active popup messages not seen by the user
        unseen_popups = PopupMessage.objects.filter(id__in=unseen_popup_ids)

        return unseen_popups
