from __future__ import annotations

from annoying.functions import get_object_or_None
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from pybb.models import Category, Forum
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
from astrobin_apps_equipment.services import EquipmentItemService
from astrobin_apps_notifications.services.notifications_service import NotificationContext
from astrobin_apps_notifications.utils import build_notification_url, push_notification
from astrobin_apps_users.services import UserService
from common.constants import GroupName
from common.services import AppRedirectionService


class EquipmentItemEditProposalViewSet(EquipmentItemViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    throttle_classes = [EquipmentEditProposalThrottle]

    def check_edit_proposal_permissions(self, request, edit_proposal, allow_self=False):
        if edit_proposal.edit_proposal_reviewed_by not in (None, request.user):
            return False, Response('This edit proposal was already reviewed by someone else', HTTP_400_BAD_REQUEST)

        if edit_proposal.edit_proposal_by == request.user and not allow_self:
            return False, Response('You cannot review an edit proposal that you proposed', HTTP_400_BAD_REQUEST)

        if edit_proposal.edit_proposal_assignee and edit_proposal.edit_proposal_assignee != request.user:
            return False, Response('You cannot review an edit proposal that is not assigned to you', HTTP_400_BAD_REQUEST)

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

    @action(detail=True, methods=['GET'], url_path='possible-assignees')
    def possible_assignees(self, request, pk):
        EditProposalModelClass = self.get_serializer().Meta.model
        edit_proposal: (EquipmentItemEditProposalMixin | EquipmentItem) = get_object_or_404(
            EditProposalModelClass, pk=pk
        )
        target_created_by: User = edit_proposal.edit_proposal_target.created_by

        value = [dict(key=target_created_by.id, value=target_created_by.userprofile.get_display_name())]

        for moderator in User.objects.filter(groups__name=GroupName.EQUIPMENT_MODERATORS):
            if moderator != edit_proposal.edit_proposal_by and moderator.pk not in [x.get('key') for x in value]:
                value.append(
                    dict(
                        key=moderator.pk,
                        value=moderator.userprofile.get_display_name(),
                    )
                )

        return Response(status=200, data=value)

    @action(detail=True, methods=['POST'])
    def assign(self, request, pk):
        EditProposalModelClass = self.get_serializer().Meta.model
        edit_proposal: (EquipmentItemEditProposalMixin | EquipmentItem) = get_object_or_404(
            EditProposalModelClass, pk=pk
        )
        item = edit_proposal.edit_proposal_target
        new_assignee_pk = request.data.get('assignee')
        new_assignee = get_object_or_None(User, pk=new_assignee_pk) if new_assignee_pk else None

        if new_assignee_pk and not new_assignee:
            return Response(f"Invalid pk: '{new_assignee_pk}'", HTTP_400_BAD_REQUEST)

        EquipmentItemService.validate_edit_proposal_assignee(
            request.user,
            dict(
                edit_proposal_target=item,
                edit_proposal_assignee=new_assignee
            ),
        )

        if edit_proposal.edit_proposal_assignee is not None and edit_proposal.edit_proposal_assignee != request.user:
            if new_assignee:
                return Response("This edit proposal has already been assigned", HTTP_400_BAD_REQUEST)
            else:
                return Response("You cannot unassign from another user", HTTP_400_BAD_REQUEST)

        edit_proposal.edit_proposal_assignee = new_assignee
        edit_proposal.save(keep_deleted=True)

        if new_assignee and new_assignee != request.user:
            push_notification(
                [new_assignee],
                request.user,
                'equipment-edit-proposal-assigned',
                {
                    'user': request.user.userprofile.get_display_name(),
                    'user_url': build_notification_url(
                        settings.BASE_URL + reverse('user_page', args=(request.user.username,))
                    ),
                    'item': f'{item.brand.name if item.brand else _("(DIY)")} {item.name}',
                    'item_url': build_notification_url(
                        AppRedirectionService.redirect(
                            f'/equipment/explorer/{EquipmentItemService(item).get_type()}/{item.pk}'
                        )
                    ),
                    'edit_proposal_url': build_notification_url(
                        AppRedirectionService.redirect(
                            f'/equipment'
                            f'/explorer'
                            f'/{item.item_type}/{item.pk}'
                            f'/{item.slug}'
                            f'/edit-proposals'
                            f'/{edit_proposal.pk}/'
                        )
                    ),
                    'extra_tags': {
                        'context': NotificationContext.EQUIPMENT
                    },
                }
            )

        serializer = self.serializer_class(edit_proposal)
        return Response(serializer.data)

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
        if edit_proposal.name != target.name and target.brand is not None and TargetModelClass.objects.filter(
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
        target.thumbnail = edit_proposal.thumbnail

        if not target.forum:
            category, created = Category.objects.get_or_create(
                name='Equipment forums',
                slug='equipment-forums',
            )

            target.forum, created = Forum.objects.get_or_create(
                category=category,
                name=f'{target}',
            )

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
                'comment': edit_proposal.edit_proposal_review_comment,
                'extra_tags': {
                    'context': NotificationContext.EQUIPMENT
                },
            }
        )

        serializer = self.serializer_class(edit_proposal)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'])
    def reject(self, request, pk):
        edit_proposal: EquipmentItemEditProposalMixin = get_object_or_404(self.get_serializer().Meta.model, pk=pk)

        if edit_proposal.edit_proposal_review_lock and edit_proposal.edit_proposal_review_lock != request.user:
            return self._conflict_response()

        check_permissions, response = self.check_edit_proposal_permissions(request, edit_proposal, allow_self=True)
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
                'comment': edit_proposal.edit_proposal_review_comment,
                'extra_tags': {
                    'context': NotificationContext.EQUIPMENT
                },
            }
        )

        serializer = self.serializer_class(edit_proposal)
        return Response(serializer.data)

    class Meta(EquipmentItemViewSet.Meta):
        abstract = True
