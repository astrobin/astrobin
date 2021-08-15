from datetime import timedelta

from annoying.functions import get_object_or_None
from celery import shared_task
from django.contrib.auth.models import User
from django.utils import timezone

from nested_comments.models import NestedComment
from nested_comments.services import CommentNotificationsService


@shared_task(time_limit=5, acks_late=True)
def notify_superuser_of_comments_pending_approval():
    now = timezone.now()
    delta = timedelta(hours=24)

    queryset = NestedComment.objects.filter(
        deleted=False,
        pending_moderation=True,
        created__range=(now - delta - timedelta(minutes=5), now - delta),
    )

    if queryset.exists():
        CommentNotificationsService.send_moderation_required_email_to_superuser()


@shared_task(time_limit=5, acks_late=True)
def auto_approve_comments():
    now = timezone.now()
    delta = timedelta(hours=36)
    superuser = get_object_or_None(User, username="astrobin")

    queryset = NestedComment.objects.filter(
        deleted=False,
        pending_moderation=True,
        created__lt=now - delta,
    )

    if queryset.exists():
        queryset.update(pending_moderation=False, moderator=superuser)
