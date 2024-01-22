from django_filters.rest_framework import FilterSet
from pybb.models import Forum, Topic


class ForumFilter(FilterSet):
    class Meta:
        model = Forum
        fields = [
            'category',
            'parent',
            'name',
            'slug',
        ]
