from typing import Union

from django.contrib.auth.models import AnonymousUser, User
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model, Q, QuerySet
from django.utils.translation import ugettext_lazy as _
from rest_framework.exceptions import PermissionDenied, ValidationError

from astrobin_apps_equipment.models.equipment_item_group import EquipmentItemKlass
from astrobin_apps_notifications.utils import build_notification_url, push_notification
from astrobin_apps_users.services import UserService
from common.constants import GroupName
from common.exceptions import Conflict
from common.services import AppRedirectionService
from toggleproperties.models import ToggleProperty


class EquipmentItemService:
    item = None

    def __init__(self, item):
        self.item = item

    def get_type(self):
        return self.item.__class__.__name__.lower()

    def get_type_label(self):
        item_type = self.get_type()
        type_map = {
            'telescope': _('Telescope'),
            'camera': _('Camera'),
            'mount': _('Mount'),
            'filter': _('Filter'),
            'accessory': _('Accessory'),
            'software': _('Software'),
        }

        return type_map.get(item_type)

    def get_users(self) -> QuerySet:
        queryset = None
        
        items = [self.item]
        
        if self.item.variant_of:
            items.append(self.item.variant_of)
            
        items += list(self.item.variants.all())

        if self.item.klass == EquipmentItemKlass.SENSOR:
            queryset = User.objects.filter(
                Q(image__imaging_cameras_2__sensor__in=items) |
                Q(image__guiding_cameras_2__sensor__in=items)
            )
        elif self.item.klass == EquipmentItemKlass.CAMERA:
            queryset = User.objects.filter(
                Q(image__imaging_cameras_2__in=items) |
                Q(image__guiding_cameras_2__in=items)
            )
        elif self.item.klass == EquipmentItemKlass.TELESCOPE:
            queryset = User.objects.filter(
                Q(image__imaging_telescopes_2__in=items) |
                Q(image__guiding_telescopes_2__in=items)
            )
        elif self.item.klass == EquipmentItemKlass.MOUNT:
            queryset = User.objects.filter(image__mounts_2__in=items)
        elif self.item.klass == EquipmentItemKlass.FILTER:
            queryset = User.objects.filter(image__filters_2__in=items)
        elif self.item.klass == EquipmentItemKlass.ACCESSORY:
            queryset = User.objects.filter(image__accessories_2__in=items)
        elif self.item.klass == EquipmentItemKlass.SOFTWARE:
            queryset = User.objects.filter(image__software_2__in=items)

        if queryset is not None:
            return queryset.distinct().order_by('pk')

    def get_followers(self) -> QuerySet:
        ct = ContentType.objects.get_for_model(self.item)
        return User.objects.filter(
            toggleproperty__object_id=self.item.pk,
            toggleproperty__content_type=ct,
            toggleproperty__property_type='follow'
        )

    def freeze_as_ambiguous(self):
        from astrobin_apps_equipment.models import EquipmentPreset

        if not self.item.frozen_as_ambiguous:
            self.item.frozen_as_ambiguous = True
            self.item.save(keep_deleted=True)

            query = None

            if self.item.klass == EquipmentItemKlass.CAMERA:
                query = Q(imaging_cameras=self.item) | Q(guiding_cameras=self.item)
            elif self.item.klass == EquipmentItemKlass.TELESCOPE:
                query = Q(imaging_telescopes=self.item) | Q(guiding_telescopes=self.item)
            elif self.item.klass == EquipmentItemKlass.MOUNT:
                query = Q(mounts=self.item)
            elif self.item.klass == EquipmentItemKlass.FILTER:
                query = Q(filters=self.item)
            elif self.item.klass == EquipmentItemKlass.ACCESSORY:
                query = Q(accessories=self.item)
            elif self.item.klass == EquipmentItemKlass.SOFTWARE:
                query = Q(software=self.item)

            if query:
                presets = EquipmentPreset.objects.filter(query).distinct()
                user_ids = presets.values_list('user', flat=True)
                users = list(User.objects.filter(id__in=user_ids))

                for preset in presets:
                    if self.item.klass == EquipmentItemKlass.CAMERA:
                        preset.imaging_cameras.remove(self.item)
                        preset.guiding_cameras.remove(self.item)
                    elif self.item.klass == EquipmentItemKlass.TELESCOPE:
                        preset.imaging_telescopes.remove(self.item)
                        preset.guiding_telescopes.remove(self.item)
                    elif self.item.klass == EquipmentItemKlass.MOUNT:
                        preset.mounts.remove(self.item)
                    elif self.item.klass == EquipmentItemKlass.FILTER:
                        preset.filters.remove(self.item)
                    elif self.item.klass == EquipmentItemKlass.ACCESSORY:
                        preset.accessories.remove(self.item)
                    elif self.item.klass == EquipmentItemKlass.SOFTWARE:
                        preset.software.remove(self.item)

                push_notification(
                    users,
                    None,
                    'ambiguous-item-removed-from-presets',
                    {
                        'item': str(self.item),
                        'item_url': build_notification_url(
                            AppRedirectionService.redirect(
                                f'/equipment/explorer/{EquipmentItemService(self.item).get_type()}/{self.item.pk}'
                            )
                        ),
                    }
                )

    def is_followed_by_user(self, user: User) -> bool:
        return ToggleProperty.objects.toggleproperties_for_object('follow', self.item, user).exists()

    @staticmethod
    def approved_or_creator_or_moderator_queryset(
            user: Union[User, AnonymousUser],
            is_equipment_moderator: bool,
            force_allow_unapproved: bool = False
    ) -> Q:
        from astrobin_apps_equipment.models.equipment_item import EquipmentItemReviewerDecision

        if force_allow_unapproved:
            return Q()

        if user and user.is_authenticated:
            if is_equipment_moderator:
                return Q()

            return Q(
                Q(reviewer_decision=EquipmentItemReviewerDecision.APPROVED) |
                Q(created_by=user)
            )

        return Q(reviewer_decision=EquipmentItemReviewerDecision.APPROVED)

    @staticmethod
    def non_diy_or_creator_or_moderator_queryset(user: Union[User, AnonymousUser], is_equipment_moderator: bool) -> Q:
        if user and user.is_authenticated:
            if is_equipment_moderator:
                return Q()

            return Q(
                Q(brand__isnull=False) |
                Q(created_by=user)
            )

        return Q(brand__isnull=False)

    @staticmethod
    def validate(user: User, attrs):
        if not UserService(user).is_in_group([GroupName.EQUIPMENT_MODERATORS, GroupName.OWN_EQUIPMENT_MIGRATORS]):
            raise PermissionDenied("You don't have permission to create or edit equipment items")

        brand = attrs['brand'] if 'brand' in attrs else None
        variant_of = attrs['variant_of'] if 'variant_of' in attrs else None
        edit_proposal_target = attrs['edit_proposal_target'] if 'edit_proposal_target' in attrs else None

        if variant_of and edit_proposal_target and variant_of == edit_proposal_target:
            raise ValidationError("An item cannot be a variant of itself")

        if brand and variant_of and brand != variant_of.brand:
            raise ValidationError("The variant needs to be in the same brand as the item")

        if not brand and variant_of:
            raise ValidationError("DIY items do not support variants")

        if variant_of and variant_of.variant_of:
            raise ValidationError("Variants do not support variants")

    @staticmethod
    def validate_edit_proposal(user: User, model: Model, attrs):
        from astrobin_apps_equipment.models import EquipmentItem

        target: EquipmentItem = attrs['edit_proposal_target']

        if target.edit_proposal_lock and target.edit_proposal_lock != user:
            raise Conflict()

        already_has_pending = model.objects.filter(
            edit_proposal_review_status__isnull=True, edit_proposal_target=target.pk
        ).exists()
        if already_has_pending:
            raise ValidationError("This item already has a pending edit proposal")

        if 'klass' not in attrs or attrs['klass'] != target.klass:
            raise ValidationError("The klass property must match that of the target item")

        if 'edit_proposal_review_status' in attrs and attrs[
            'edit_proposal_review_status'] is not None:
            raise ValidationError("The edit_proposal_review_status must be null")

        EquipmentItemService.validate_edit_proposal_assignee(user, attrs)

    @staticmethod
    def validate_edit_proposal_assignee(user: User, attrs):
        from astrobin_apps_equipment.models import EquipmentItem

        target: EquipmentItem = attrs['edit_proposal_target']

        if 'edit_proposal_assignee' in attrs and attrs['edit_proposal_assignee'] is not None:
            assignee = attrs['edit_proposal_assignee']
            if assignee == user:
                raise ValidationError("An edit proposal cannot be assigned to its creator")

            if assignee != target.created_by and not assignee.groups.filter(
                    name=GroupName.EQUIPMENT_MODERATORS
            ).exists():
                raise ValidationError("An edit proposal can only be assigned to a moderator or the item's creator")
