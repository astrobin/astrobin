from django_filters.rest_framework import FilterSet
from pybb.models import Topic


class TopicFilter(FilterSet):
    class Meta:
        model = Topic
        fields = [
            'user',
            'on_moderation',
            'forum',
            'name',
        ]
