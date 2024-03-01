import django_filters
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, QuerySet
from django_filters.rest_framework import FilterSet

from astrobin_apps_users.services import UserService
from common.constants import GroupName
from toggleproperties.models import ToggleProperty


class EquipmentItemFilter(FilterSet):
    pending_review = django_filters.BooleanFilter(method='has_pending_review')
    pending_edit = django_filters.BooleanFilter(method='has_pending_edit_proposals')
    followed = django_filters.BooleanFilter(method='is_followed')

    def has_pending_review(self, queryset: QuerySet, value, *args, **kwargs):
        condition = args[0]

        is_authenticated: bool = self.request.user.is_authenticated
        is_moderator: bool = UserService(self.request.user).is_in_group(GroupName.EQUIPMENT_MODERATORS)

        if not is_authenticated or not is_moderator:
            return queryset.none()

        queryset = queryset.exclude(Q(created_by=self.request.user))

        if condition:
            queryset = queryset.filter(reviewer_decision__isnull=True).order_by('-created')

        return queryset

    def has_pending_edit_proposals(self, queryset: QuerySet, value, *args, **kwargs):
        condition = args[0]

        if condition:
            queryset = queryset.filter(edit_proposals__gt=0)
        else:
            queryset = queryset.exclude(edit_proposals__gt=0)

        queryset = queryset.filter(
            edit_proposals__deleted__isnull=True,
            edit_proposals__edit_proposal_review_status__isnull=True,
        )

        if self.request.user.is_authenticated:
            queryset = queryset.exclude(edit_proposals__edit_proposal_by=self.request.user)

        return queryset.distinct().order_by('-created')

    def is_followed(self, queryset: QuerySet, value, *args, **kwargs):
        condition = args[0]

        if self.request.user.is_anonymous:
            return queryset.none()

        if condition:
            toggle_properties = ToggleProperty.objects.filter(
                user=self.request.user,
                property_type='follow',
                content_type=ContentType.objects.get_for_model(self.Meta.model),
            )
            queryset = queryset.filter(pk__in=[int(x) for x in toggle_properties.values_list('object_id', flat=True)])

        return queryset.distinct().order_by('-created')

    class Meta:
        abstract = True
        fields = ['brand', 'name', 'pending_review', 'pending_edit']
