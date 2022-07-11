from __future__ import annotations

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN, HTTP_409_CONFLICT

from astrobin_apps_equipment.api.throttle.equipment_edit_proposal_throttle import EquipmentEditProposalThrottle
from astrobin_apps_equipment.api.views.equipment_item_view_set import EquipmentItemViewSet
from astrobin_apps_equipment.models import EquipmentItem
from astrobin_apps_equipment.models.equipment_item_edit_proposal_mixin import EquipmentItemEditProposalMixin
from astrobin_apps_users.services import UserService
from common.constants import GroupName
from astrobin_apps_notifications.utils import build_notification_url, push_notification
from common.services import AppRedirectionService


class EquipmentItemEditProposalViewSet(EquipmentItemViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    throttle_classes = [EquipmentEditProposalThrottle]

    def check_edit_proposal_permissions(self, request, edit_proposal):
        if edit_proposal.edit_proposal_reviewed_by not in (None, request.user):
            return False, Response('This edit proposal was already reviewed by someone else', HTTP_400_BAD_REQUEST)

        if edit_proposal.edit_proposal_by == request.user:
            return False, Response('You cannot review an edit proposal that you proposed', HTTP_400_BAD_REQUEST)

        return True, None

    @action(detail=True, methods=['POST'], url_path='acquire-review-lock')
    def acquire_review_lock(self, request, pk):
        if not UserService(request.user).is_in_group(GroupName.OWN_EQUIPMENT_MIGRATORS):
            raise PermissionDenied(request.user)

        edit_proposal: EquipmentItemEditProposalMixin = self.get_object()

        if edit_proposal.edit_proposal_review_lock and edit_proposal.edit_proposal_review_lock != request.user:
            return self._conflict_response()

        edit_proposal.edit_proposal_review_lock = request.user
        edit_proposal.edit_proposal_review_lock_timestamp = timezone.now()
        edit_proposal.save(keep_deleted=True)

        return Response(status=HTTP_200_OK)

    @action(detail=True, methods=['POST'], url_path='release-review-lock')
    def release_review_lock(self, request, pk):
        edit_proposal: EquipmentItemEditProposalMixin = self.get_object()

        if edit_proposal.edit_proposal_review_lock == request.user:
            edit_proposal.edit_proposal_review_lock = None
            edit_proposal.edit_proposal_review_lock_timestamp = None
            edit_proposal.save(keep_deleted=True)

        return Response(status=HTTP_200_OK)

    def approve(self, request, pk):
        EditProposalModelClass = self.get_serializer().Meta.model

        edit_proposal: (EquipmentItemEditProposalMixin | EquipmentItem) = get_object_or_404(
            EditProposalModelClass, pk=pk
        )

        if edit_proposal.edit_proposal_review_lock and edit_proposal.edit_proposal_review_lock != request.user:
            return self._conflict_response()

        check_permissions, response = self.check_edit_proposal_permissions(request, edit_proposal)
        if not check_permissions:
            return response

        target: EquipmentItem = edit_proposal.edit_proposal_target
        TargetModelClass = type(target)
        if edit_proposal.name != target.name and TargetModelClass.objects.filter(
                brand=target.brand, name=edit_proposal.name
        ).exclude(pk=target.pk).exists():
            return Response(
                _(
                    "This edit proposal cannot be approved because an item with this brand and name already exists. Please reject it."
                ),
                status=HTTP_409_CONFLICT
            )

        if target.name != edit_proposal.name and \
                not UserService(request.user).is_in_group(GroupName.EQUIPMENT_MODERATORS) and \
                not UserService(edit_proposal.created_by).is_in_group(GroupName.EQUIPMENT_MODERATORS) and \
                not target.reviewer_decision is None:
            return Response(
                _(
                    "This edit proposal needs to be approved by a moderator because it changes the name of the item."
                ),
                status=HTTP_403_FORBIDDEN
            )

        edit_proposal.edit_proposal_reviewed_by = request.user
        edit_proposal.edit_proposal_review_ip = request.META.get('REMOTE_ADDR')
        edit_proposal.edit_proposal_review_timestamp = timezone.now()
        edit_proposal.edit_proposal_review_comment = request.data.get('comment')
        edit_proposal.edit_proposal_review_status = 'APPROVED'

        target.name = edit_proposal.name
        target.community_notes = edit_proposal.community_notes
        target.variant_of = edit_proposal.variant_of
        target.website = edit_proposal.website
        target.image = edit_proposal.image

        target.save()
        edit_proposal.save()

        push_notification(
            [x for x in list({edit_proposal.edit_proposal_by, target.created_by}) if x != request.user],
            request.user,
            'equipment-edit-proposal-approved',
            {
                'user': request.user.userprofile.get_display_name(),
                'user_url': build_notification_url(
                    settings.BASE_URL + reverse('user_page', args=(request.user.username,))
                ),
                'item': f'{target.brand.name if target.brand else _("(DIY)")} {target.name}',
                'item_url': build_notification_url(
                    AppRedirectionService.redirect(
                        f'/equipment'
                        f'/explorer'
                        f'/{target.item_type}/{target.pk}'
                        f'/{target.slug}'
                    )
                ),
                'edit_proposal_url': build_notification_url(
                    AppRedirectionService.redirect(
                        f'/equipment'
                        f'/explorer'
                        f'/{target.item_type}/{target.pk}'
                        f'/{target.slug}'
                        f'/edit-proposals'
                        f'/{edit_proposal.pk}/'
                    )
                ),
                'comment': edit_proposal.edit_proposal_review_comment
            }
        )

        serializer = self.serializer_class(edit_proposal)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'])
    def reject(self, request, pk):
        edit_proposal: EquipmentItemEditProposalMixin = get_object_or_404(self.get_serializer().Meta.model, pk=pk)

        if edit_proposal.edit_proposal_review_lock and edit_proposal.edit_proposal_review_lock != request.user:
            return self._conflict_response()

        check_permissions, response = self.check_edit_proposal_permissions(request, edit_proposal)
        if not check_permissions:
            return response

        edit_proposal.edit_proposal_reviewed_by = request.user
        edit_proposal.edit_proposal_review_ip = request.META.get('REMOTE_ADDR')
        edit_proposal.edit_proposal_review_timestamp = timezone.now()
        edit_proposal.edit_proposal_review_comment = request.data.get('comment')
        edit_proposal.edit_proposal_review_status = 'REJECTED'

        edit_proposal.save()

        target = edit_proposal.edit_proposal_target

        push_notification(
            [x for x in list({edit_proposal.edit_proposal_by, target.created_by}) if x != request.user],
            request.user,
            'equipment-edit-proposal-rejected',
            {
                'user': request.user.userprofile.get_display_name(),
                'user_url': build_notification_url(
                    settings.BASE_URL + reverse('user_page', args=(request.user.username,))
                ),
                'item': f'{target.brand.name if target.brand else _("(DIY)")} {target.name}',
                'item_url': build_notification_url(
                    AppRedirectionService.redirect(
                        f'/equipment'
                        f'/explorer'
                        f'/{target.item_type}/{target.pk}'
                        f'/{target.slug}'
                    )
                ),
                'edit_proposal_url': build_notification_url(
                    AppRedirectionService.redirect(
                        f'/equipment'
                        f'/explorer'
                        f'/{target.item_type}/{target.pk}'
                        f'/{target.slug}'
                        f'/edit-proposals'
                        f'/{edit_proposal.pk}/'
                    )
                ),
                'comment': edit_proposal.edit_proposal_review_comment
            }
        )

        serializer = self.serializer_class(edit_proposal)
        return Response(serializer.data)

    class Meta(EquipmentItemViewSet.Meta):
        abstract = True
