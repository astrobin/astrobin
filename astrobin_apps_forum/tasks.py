from annoying.functions import get_object_or_None
from celery import shared_task
from pybb.models import Topic

from astrobin_apps_forum.services import ForumService


@shared_task(acks_late=True)
def notify_equipment_users(topic_id: int) -> None:
    topic: Topic = get_object_or_None(Topic, id=topic_id)
    if topic:
        ForumService.notify_equipment_users(topic)
