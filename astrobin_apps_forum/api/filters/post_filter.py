from django_filters.rest_framework import FilterSet
from pybb.models import Post


class PostFilter(FilterSet):
    class Meta:
        model = Post
        fields = ['user', 'on_moderation']
