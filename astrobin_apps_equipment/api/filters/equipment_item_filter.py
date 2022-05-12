import django_filters
from django.db.models import Q, QuerySet
from django_filters.rest_framework import FilterSet


class EquipmentItemFilter(FilterSet):
    pending_review = django_filters.BooleanFilter(method='has_pending_review')
    pending_edit = django_filters.BooleanFilter(method='has_pending_edit_proposals')

    def has_pending_review(self, queryset: QuerySet, value, *args, **kwargs):
        condition = args[0]

        is_authenticated: bool = self.request.user.is_authenticated
        is_moderator: bool = is_authenticated and self.request.user.groups.filter(name='equipment_moderators').exists()

        if not is_authenticated or not is_moderator:
            return queryset.none()

        queryset = queryset.exclude(Q(created_by=self.request.user) | Q(brand__isnull=True))

        if condition:
            queryset = queryset.filter(reviewer_decision__isnull=True)

        return queryset

    def has_pending_edit_proposals(self, queryset: QuerySet, value, *args, **kwargs):
        condition = args[0]

        if condition:
            queryset = queryset.filter(edit_proposals__gt=0)
        else:
            queryset = queryset.exclude(edit_proposals__gt=0)

        return queryset.filter(
            edit_proposals__deleted__isnull=True,
            edit_proposals__edit_proposal_review_status__isnull=True
        ).distinct()

    class Meta:
        abstract = True
        fields = ['name', 'pending_review', 'pending_edit']
