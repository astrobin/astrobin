import django_filters
from django_filters.rest_framework import FilterSet


class EquipmentItemFilter(FilterSet):
    pending_review = django_filters.BooleanFilter(method='has_pending_review')
    pending_edit = django_filters.BooleanFilter(method='has_pending_edit_proposals')

    def has_pending_review(self, queryset, value, *args, **kwargs):
        condition = args[0]

        if condition:
            queryset = queryset.filter(reviewer_decision__isnull=True)
            if self.request.user.is_authenticated:
                queryset = queryset.exclude(created_by=self.request.user)

        return queryset

    def has_pending_edit_proposals(self, queryset, value, *args, **kwargs):
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
