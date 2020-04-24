# Python
import datetime

# Django
from django.db.models import Q

# Third party
try:
    from actstream.models import Action
    from actstream import action
except:
    pass


def add_story(actor, **kwargs):
    if Action is None or action is None:
        return

    date_from = datetime.datetime.now() - datetime.timedelta(days=7)
    verb = kwargs['verb']

    # Delete previous stories with the same action object
    def clear_as_action_object(kwargs):
        if 'action_object' in kwargs:
            Action.objects.filter(
                Q(action_object_object_id = kwargs['action_object'].pk) |
                Q(target_object_id = kwargs['action_object'].pk),
                timestamp__gte = date_from).delete()

    # Delete previous stories with the same target
    def clear_as_target(kwargs):
        if 'target' in kwargs:
            Action.objects.filter(
                Q(action_object_object_id = kwargs['target'].pk) |
                Q(target_object_id = kwargs['target'].pk),
                timestamp__gte = date_from).delete()

    CLEAR_AS_ACTION_OBJECT_VERBS = [
        'VERB_UPLOADED_IMAGE',
        'VERB_UPLOADED_REVISION',
        'VERB_LIKED_IMAGE',
        'VERB_BOOKMARKED_IMAGE',
        'VERB_COMMENTED_IMAGE',
    ]

    CLEAR_AS_TARGET_VERBS = [
        'VERB_UPLOADED_IMAGE',
        'VERB_UPLOADED_REVISION',
        'VERB_LIKED_IMAGE',
        'VERB_BOOKMARKED_IMAGE',
        'VERB_COMMENTED_IMAGE',
    ]

    DONT_CLEAR_VERBS = [
    ]

    if verb in CLEAR_AS_ACTION_OBJECT_VERBS:
        clear_as_action_object(kwargs)

    if verb in CLEAR_AS_TARGET_VERBS:
        clear_as_target(kwargs)

    if verb in DONT_CLEAR_VERBS:
        pass

    action.send(actor, **kwargs)
