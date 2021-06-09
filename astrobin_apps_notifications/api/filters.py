from django_filters import FilterSet
from persistent_messages.models import Message


class NotificationFilter(FilterSet):
    class Meta:
        model = Message
        fields = ('read',)
