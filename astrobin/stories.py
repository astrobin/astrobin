# Python
import datetime

from django.contrib.contenttypes.models import ContentType
# Django
from django.db.models import Q

# Third party
try:
    from actstream.models import Action
    from actstream import action
except ImportError:
    Action = None
    action = None
    pass

ACTSTREAM_VERB_UPLOADED_IMAGE = 'VERB_UPLOADED_IMAGE'
ACTSTREAM_VERB_UPLOADED_REVISION = 'VERB_UPLOADED_REVISION'
ACTSTREAM_VERB_LIKED_IMAGE = 'VERB_LIKED_IMAGE'
ACTSTREAM_VERB_BOOKMARKED_IMAGE = 'VERB_BOOKMARKED_IMAGE'
ACTSTREAM_VERB_COMMENTED_IMAGE = 'VERB_COMMENTED_IMAGE'
ACTSTREAM_VERB_CREATED_PUBLIC_GROUP = 'VERB_CREATED_PUBLIC_GROUP'
ACTSTREAM_VERB_JOINED_GROUP = 'VERB_JOINED_GROUP'
ACTSTREAM_VERB_CREATED_MARKETPLACE_LISTING = 'VERB_CREATED_MARKETPLACE_LISTING'

CLEAR_AS_ACTION_OBJECT_VERBS = [
    ACTSTREAM_VERB_UPLOADED_IMAGE,
    ACTSTREAM_VERB_UPLOADED_REVISION,
    ACTSTREAM_VERB_LIKED_IMAGE,
    ACTSTREAM_VERB_BOOKMARKED_IMAGE,
    ACTSTREAM_VERB_COMMENTED_IMAGE,
]

CLEAR_AS_TARGET_VERBS = [
    ACTSTREAM_VERB_UPLOADED_IMAGE,
    ACTSTREAM_VERB_UPLOADED_REVISION,
    ACTSTREAM_VERB_LIKED_IMAGE,
    ACTSTREAM_VERB_BOOKMARKED_IMAGE,
    ACTSTREAM_VERB_COMMENTED_IMAGE,
]

DONT_CLEAR_VERBS = [
    ACTSTREAM_VERB_CREATED_MARKETPLACE_LISTING
]


def add_story(actor, **kwargs) -> None:
    if Action is None or action is None:
        return

    verb = kwargs['verb']

    # Delete previous stories with the same action object
    def clear_as_action_object(kwargs) -> None:
        if 'action_object' in kwargs:
            object_id = kwargs['action_object'].pk
            ct = ContentType.objects.get_for_model(kwargs['action_object'])
            Action.objects.filter(
                Q(
                    Q(action_object_object_id=object_id) &
                    Q(action_object_content_type_id=ct.id)
                ) |
                Q(
                    Q(target_object_id=object_id) &
                    Q(target_content_type_id=ct.id)
                )
            ).delete()

    # Delete previous stories with the same target
    def clear_as_target(kwargs) -> None:
        if 'target' in kwargs:
            object_id = kwargs['target'].pk
            ct = ContentType.objects.get_for_model(kwargs['target'])
            Action.objects.filter(
                Q(
                    Q(target_object_id=object_id) &
                    Q(target_content_type_id=ct.id)
                ) |
                Q(
                    Q(action_object_object_id=object_id) &
                    Q(action_object_content_type_id=ct.id)
                )
            ).delete()

    if verb in CLEAR_AS_ACTION_OBJECT_VERBS:
        clear_as_action_object(kwargs)

    if verb in CLEAR_AS_TARGET_VERBS:
        clear_as_target(kwargs)

    action.send(actor, **kwargs)
