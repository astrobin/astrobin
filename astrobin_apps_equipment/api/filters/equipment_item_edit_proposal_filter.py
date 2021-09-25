import django_filters
from django_filters.rest_framework import FilterSet


class EquipmentItemEditProposalFilter(FilterSet):
    pending = django_filters.BooleanFilter(field_name='edit_proposal_review_status', lookup_expr='isnull')

    class Meta:
        abstract = True
        fields = {
            'edit_proposal_target': ["exact"],
            'edit_proposal_review_status': ["exact"],

        }
