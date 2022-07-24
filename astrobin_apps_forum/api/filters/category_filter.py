from django_filters.rest_framework import FilterSet
from pybb.models import Category


class CategoryFilter(FilterSet):
    class Meta:
        model = Category
        fields = [
            'name',
        ]
