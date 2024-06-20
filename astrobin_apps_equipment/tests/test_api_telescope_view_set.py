import mock
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from pybb.models import Topic
from rest_framework.test import APIClient

from astrobin.tests.generators import Generators
from astrobin_apps_equipment.models import EquipmentBrand, Telescope
from astrobin_apps_equipment.models.equipment_item import EquipmentItemRejectionReason, EquipmentItemReviewerDecision
from astrobin_apps_equipment.models.equipment_item_group import EquipmentItemKlass, EquipmentItemUsageType
from astrobin_apps_equipment.models.telescope_base_model import TelescopeType
from astrobin_apps_equipment.services import EquipmentItemService, EquipmentService
from astrobin_apps_equipment.tests.equipment_generators import EquipmentGenerators
from common.constants import GroupName


class TestApiTelescopeViewSet(TestCase):
    def test_list_with_no_items(self):
        client = APIClient()

        response = client.get(reverse('astrobin_apps_equipment:telescope-list'), format='json')
        self.assertEquals(0, response.data['count'])

    def test_list_with_items(self):
        client = APIClient()

        telescope = EquipmentGenerators.telescope(reviewer_decision=EquipmentItemReviewerDecision.APPROVED)

        response = client.get(reverse('astrobin_apps_equipment:telescope-list'), format='json')
        self.assertEquals(1, response.data['count'])
        self.assertEquals(telescope.name, response.data['results'][0]['name'])

    def test_list_diy(self):
        client = APIClient()

        telescope = EquipmentGenerators.telescope(reviewer_decision=EquipmentItemReviewerDecision.APPROVED)
        Telescope.objects.filter(pk=telescope.pk).update(brand=None)

        response = client.get(reverse('astrobin_apps_equipment:telescope-list'), format='json')
        self.assertEquals(0, response.data['count'])

    def test_list_diy_but_creator(self):
        client = APIClient()

        user = Generators.user()
        telescope = EquipmentGenerators.telescope(
            reviewer_decision=EquipmentItemReviewerDecision.APPROVED,
            created_by=user
        )
        Telescope.objects.filter(pk=telescope.pk).update(brand=None)

        client.login(username=user.username, password=user.password)
        client.force_authenticate(user=user)

        response = client.get(reverse('astrobin_apps_equipment:telescope-list'), format='json')
        self.assertEquals(1, response.data['count'])
        self.assertEquals(telescope.name, response.data['results'][0]['name'])

    def test_list_diy_but_moderator(self):
        client = APIClient()

        user = Generators.user(groups=[GroupName.EQUIPMENT_MODERATORS])
        telescope = EquipmentGenerators.telescope(reviewer_decision=EquipmentItemReviewerDecision.APPROVED)
        Telescope.objects.filter(pk=telescope.pk).update(brand=None)

        client.login(username=user.username, password=user.password)
        client.force_authenticate(user=user)

        response = client.get(reverse('astrobin_apps_equipment:telescope-list'), format='json')
        self.assertEquals(1, response.data['count'])
        self.assertEquals(telescope.name, response.data['results'][0]['name'])

    def test_list_diy_but_override(self):
        client = APIClient()

        telescope = EquipmentGenerators.telescope(reviewer_decision=EquipmentItemReviewerDecision.APPROVED)
        Telescope.objects.filter(pk=telescope.pk).update(brand=None)

        response = client.get(reverse('astrobin_apps_equipment:telescope-list') + '?allow-DIY=true', format='json')
        self.assertEquals(1, response.data['count'])
        self.assertEquals(telescope.name, response.data['results'][0]['name'])

    def test_list_unapproved(self):
        client = APIClient()

        EquipmentGenerators.telescope(reviewer_decision=None)

        response = client.get(reverse('astrobin_apps_equipment:telescope-list'), format='json')
        self.assertEquals(0, response.data['count'])

    def test_list_unapproved_but_creator(self):
        client = APIClient()

        user = Generators.user()

        telescope = EquipmentGenerators.telescope(reviewer_decision=None, created_by=user)

        client.login(username=user.username, password=user.password)
        client.force_authenticate(user=user)

        response = client.get(reverse('astrobin_apps_equipment:telescope-list'), format='json')

        self.assertEquals(1, response.data['count'])
        self.assertEquals(telescope.name, response.data['results'][0]['name'])

    def test_list_unapproved_but_moderator(self):
        client = APIClient()

        user = Generators.user(groups=[GroupName.EQUIPMENT_MODERATORS])

        telescope = EquipmentGenerators.telescope(reviewer_decision=None)

        client.login(username=user.username, password=user.password)
        client.force_authenticate(user=user)

        response = client.get(
            reverse('astrobin_apps_equipment:telescope-list'), format='json'
        )

        self.assertEquals(1, response.data['count'])
        self.assertEquals(telescope.name, response.data['results'][0]['name'])

    def test_list_unapproved_but_override(self):
        client = APIClient()

        user = Generators.user()

        telescope = EquipmentGenerators.telescope(reviewer_decision=None)

        client.login(username=user.username, password=user.password)
        client.force_authenticate(user=user)

        response = client.get(
            reverse('astrobin_apps_equipment:telescope-list') + '?allow-unapproved=true', format='json'
        )

        self.assertEquals(1, response.data['count'])
        self.assertEquals(telescope.name, response.data['results'][0]['name'])

    def test_serializer_no_variants(self):
        client = APIClient()

        EquipmentGenerators.telescope(reviewer_decision=EquipmentItemReviewerDecision.APPROVED)

        response = client.get(reverse('astrobin_apps_equipment:telescope-list'), format='json')

        self.assertEquals(0, len(response.data['results'][0]['variants']))

    def test_serializer_one_variant(self):
        client = APIClient()

        telescope = EquipmentGenerators.telescope(reviewer_decision=EquipmentItemReviewerDecision.APPROVED)
        variant = EquipmentGenerators.telescope(
            reviewer_decision=EquipmentItemReviewerDecision.APPROVED,
            variant_of=telescope
        )

        response = client.get(
            reverse('astrobin_apps_equipment:telescope-detail', args=(telescope.id,)), format='json'
        )

        self.assertEquals(200, response.status_code)
        self.assertEquals(1, len(response.data['variants']))
        self.assertEquals(variant.name, response.data['variants'][0]['name'])

    def test_serializer_diy_variant(self):
        client = APIClient()

        telescope = EquipmentGenerators.telescope(reviewer_decision=EquipmentItemReviewerDecision.APPROVED)
        variant = EquipmentGenerators.telescope(
            reviewer_decision=EquipmentItemReviewerDecision.APPROVED,
            variant_of=telescope
        )

        Telescope.objects.filter(pk=variant.pk).update(brand=None)

        response = client.get(
            reverse('astrobin_apps_equipment:telescope-detail', args=(telescope.id,)), format='json'
        )

        self.assertEquals(200, response.status_code)
        self.assertEquals(0, len(response.data['variants']))

    def test_serializer_diy_variant_but_creator(self):
        client = APIClient()

        user = Generators.user()
        telescope = EquipmentGenerators.telescope(reviewer_decision=EquipmentItemReviewerDecision.APPROVED)
        variant = EquipmentGenerators.telescope(
            reviewer_decision=EquipmentItemReviewerDecision.APPROVED,
            variant_of=telescope,
            created_by=user
        )

        Telescope.objects.filter(pk=variant.pk).update(brand=None)

        client.login(username=user.username, password=user.password)
        client.force_authenticate(user=user)

        response = client.get(
            reverse('astrobin_apps_equipment:telescope-detail', args=(telescope.id,)), format='json'
        )

        self.assertEquals(200, response.status_code)
        self.assertEquals(1, len(response.data['variants']))
        self.assertEquals(variant.name, response.data['variants'][0]['name'])

    def test_serializer_unapproved_variant(self):
        client = APIClient()

        telescope = EquipmentGenerators.telescope(reviewer_decision=EquipmentItemReviewerDecision.APPROVED)
        EquipmentGenerators.telescope(
            reviewer_decision=None,
            variant_of=telescope
        )

        response = client.get(
            reverse('astrobin_apps_equipment:telescope-detail', args=(telescope.id,)), format='json'
        )

        self.assertEquals(200, response.status_code)
        self.assertEquals(0, len(response.data['variants']))

    def test_serializer_unapproved_variant_but_creator(self):
        client = APIClient()

        user = Generators.user()
        telescope = EquipmentGenerators.telescope(reviewer_decision=EquipmentItemReviewerDecision.APPROVED)
        variant = EquipmentGenerators.telescope(
            reviewer_decision=None,
            variant_of=telescope,
            created_by=user
        )

        client.login(username=user.username, password=user.password)
        client.force_authenticate(user=user)

        response = client.get(
            reverse('astrobin_apps_equipment:telescope-detail', args=(telescope.id,)), format='json'
        )

        self.assertEquals(200, response.status_code)
        self.assertEquals(1, len(response.data['variants']))
        self.assertEquals(variant.name, response.data['variants'][0]['name'])

    def test_serializer_unapproved_variant_but_override(self):
        client = APIClient()

        telescope = EquipmentGenerators.telescope(reviewer_decision=EquipmentItemReviewerDecision.APPROVED)
        variant = EquipmentGenerators.telescope(
            reviewer_decision=None,
            variant_of=telescope,
        )

        response = client.get(
            reverse('astrobin_apps_equipment:telescope-detail', args=(telescope.pk,)) + '?allow-unapproved=true',
            format='json'
        )

        self.assertEquals(200, response.status_code)
        self.assertEquals(1, len(response.data['variants']))
        self.assertEquals(variant.name, response.data['variants'][0]['name'])

    def test_viewset_no_variants(self):
        client = APIClient()

        telescope = EquipmentGenerators.telescope(reviewer_decision=EquipmentItemReviewerDecision.APPROVED)

        response = client.get(
            reverse('astrobin_apps_equipment:telescope-detail', args=(telescope.pk,)) + 'variants/', format='json'
        )

        self.assertEquals(200, response.status_code)
        self.assertEquals(0, len(response.data))

    def test_viewset_one_variant(self):
        client = APIClient()

        telescope = EquipmentGenerators.telescope(reviewer_decision=EquipmentItemReviewerDecision.APPROVED)
        variant = EquipmentGenerators.telescope(
            reviewer_decision=EquipmentItemReviewerDecision.APPROVED,
            variant_of=telescope
        )

        response = client.get(
            reverse('astrobin_apps_equipment:telescope-detail', args=(telescope.pk,)) + 'variants/', format='json'
        )

        self.assertEquals(200, response.status_code)
        self.assertEquals(1, len(response.data))
        self.assertEquals(variant.name, response.data[0]['name'])

    def test_viewset_unapproved_variant(self):
        client = APIClient()

        telescope = EquipmentGenerators.telescope(reviewer_decision=EquipmentItemReviewerDecision.APPROVED)
        EquipmentGenerators.telescope(
            reviewer_decision=None,
            variant_of=telescope
        )

        response = client.get(
            reverse('astrobin_apps_equipment:telescope-detail', args=(telescope.pk,)) + 'variants/', format='json'
        )

        self.assertEquals(200, response.status_code)
        self.assertEquals(0, len(response.data))

    def test_viewset_unapproved_variant_but_creator(self):
        client = APIClient()

        user = Generators.user()
        telescope = EquipmentGenerators.telescope(reviewer_decision=EquipmentItemReviewerDecision.APPROVED)
        variant = EquipmentGenerators.telescope(
            reviewer_decision=None,
            variant_of=telescope,
            created_by=user
        )

        client.login(username=user.username, password=user.password)
        client.force_authenticate(user=user)

        response = client.get(
            reverse('astrobin_apps_equipment:telescope-detail', args=(telescope.pk,)) + 'variants/', format='json'
        )

        self.assertEquals(200, response.status_code)
        self.assertEquals(1, len(response.data))
        self.assertEquals(variant.name, response.data[0]['name'])

    def test_viewset_unapproved_variant_but_moderator(self):
        client = APIClient()

        user = Generators.user(groups=[GroupName.EQUIPMENT_MODERATORS])
        telescope = EquipmentGenerators.telescope(reviewer_decision=EquipmentItemReviewerDecision.APPROVED)
        variant = EquipmentGenerators.telescope(
            reviewer_decision=None,
            variant_of=telescope
        )

        client.login(username=user.username, password=user.password)
        client.force_authenticate(user=user)

        response = client.get(
            reverse('astrobin_apps_equipment:telescope-detail', args=(telescope.pk,)) + 'variants/', format='json'
        )

        self.assertEquals(200, response.status_code)
        self.assertEquals(1, len(response.data))
        self.assertEquals(variant.name, response.data[0]['name'])

    def test_viewset_unapproved_variant_but_override(self):
        client = APIClient()

        telescope = EquipmentGenerators.telescope(reviewer_decision=EquipmentItemReviewerDecision.APPROVED)
        variant = EquipmentGenerators.telescope(
            reviewer_decision=None,
            variant_of=telescope
        )

        response = client.get(
            reverse(
                'astrobin_apps_equipment:telescope-detail', args=(telescope.pk,)
            ) + 'variants/?allow-unapproved=true',
            format='json'
        )

        self.assertEquals(200, response.status_code)
        self.assertEquals(1, len(response.data))
        self.assertEquals(variant.name, response.data[0]['name'])

    def test_deleting_not_allowed(self):
        client = APIClient()

        telescope = EquipmentGenerators.telescope()

        response = client.delete(
            reverse('astrobin_apps_equipment:telescope-detail', args=(telescope.pk,)), format='json'
        )
        self.assertEquals(405, response.status_code)

        user = Generators.user(groups=[GroupName.EQUIPMENT_MODERATORS])
        client.login(username=user.username, password=user.password)
        client.force_authenticate(user=user)

        response = client.delete(
            reverse('astrobin_apps_equipment:telescope-detail', args=(telescope.pk,)), format='json'
        )
        self.assertEquals(405, response.status_code)

    def test_post_not_allowed(self):
        client = APIClient()

        response = client.post(
            reverse('astrobin_apps_equipment:telescope-list'), {
                'brand': EquipmentGenerators.brand().pk,
                'name': 'telescope Foo',
                'type': TelescopeType.REFRACTOR_ACHROMATIC,
            }, format='json'
        )
        self.assertEquals(403, response.status_code)

        user = Generators.user()
        client.login(username=user.username, password=user.password)
        client.force_authenticate(user=user)

        response = client.post(
            reverse('astrobin_apps_equipment:telescope-list'), {
                'brand': EquipmentGenerators.brand().pk,
                'name': 'telescope Foo',
                'type': TelescopeType.REFRACTOR_ACHROMATIC,
            }, format='json'
        )
        self.assertEquals(403, response.status_code)

    def test_created_by(self):
        client = APIClient()

        user = Generators.user(groups=[GroupName.EQUIPMENT_MODERATORS])
        client.login(username=user.username, password=user.password)
        client.force_authenticate(user=user)

        response = client.post(
            reverse('astrobin_apps_equipment:telescope-list'), {
                'brand': EquipmentGenerators.brand().pk,
                'name': 'telescope Foo',
                'type': TelescopeType.REFRACTOR_ACHROMATIC,
            }, format='json'
        )
        self.assertEquals(201, response.status_code)
        self.assertEquals(user.pk, response.data['created_by'])

    def test_list_returns_only_own_DIYs(self):
        user = Generators.user()
        first = EquipmentGenerators.telescope(created_by=user)
        first.brand = None
        first.save()

        second = EquipmentGenerators.telescope()
        second.brand = None
        second.save()

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get(reverse('astrobin_apps_equipment:telescope-list'), format='json')
        self.assertEquals(1, response.data['count'])
        self.assertEquals(first.name, response.data['results'][0]['name'])

    def test_find_recently_used_no_usages(self):
        user = Generators.user()

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get(
            reverse('astrobin_apps_equipment:telescope-list') + 'recently-used/?usage-type=imaging', format='json'
        )

        self.assertEquals(0, len(response.data))

    def test_find_recently_used_one_usage(self):
        user = Generators.user()
        telescope = EquipmentGenerators.telescope(created_by=user)
        image = Generators.image(user=user)
        image.imaging_telescopes_2.add(telescope)

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get(
            reverse('astrobin_apps_equipment:telescope-list') + 'recently-used/?usage-type=imaging', format='json'
        )

        self.assertEquals(1, len(response.data))

    def test_find_recently_used_wrong_usage_type(self):
        user = Generators.user()
        telescope = EquipmentGenerators.telescope(created_by=user)
        image = Generators.image(user=user)
        image.imaging_telescopes_2.add(telescope)

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get(
            reverse('astrobin_apps_equipment:telescope-list') + 'recently-used/?usage-type=guiding', format='json'
        )

        self.assertEquals(0, len(response.data))

    @mock.patch("astrobin_apps_equipment.services.equipment_service.push_notification")
    def test_reject(self, push_notification):
        user = Generators.user()
        moderator = Generators.user(groups=[GroupName.EQUIPMENT_MODERATORS])
        telescope = EquipmentGenerators.telescope(created_by=user)
        image = Generators.image(user=user)
        image.imaging_telescopes_2.add(telescope)

        client = APIClient()
        client.force_authenticate(user=moderator)

        push_notification.reset_mock()

        client.post(
            reverse('astrobin_apps_equipment:telescope-detail', args=(telescope.pk,)) + 'reject/'
        )

        self.assertFalse(Telescope.objects.filter(pk=telescope.pk).exists())

        self.assertFalse(EquipmentBrand.objects.filter(pk=telescope.brand.pk).exists())

        push_notification.assert_has_calls(
            [
                mock.call([user], moderator, 'equipment-item-rejected', mock.ANY),
                mock.call([user], moderator, 'equipment-item-rejected-affected-image', mock.ANY),
            ], any_order=True
        )

    def test_reject_approved_move_forum_topics(self):
        user = Generators.user()
        moderator = Generators.user(groups=[GroupName.EQUIPMENT_MODERATORS])
        telescope1 = EquipmentGenerators.telescope(created_by=user, reviewer_decision=EquipmentItemReviewerDecision.APPROVED)
        telescope2 = EquipmentGenerators.telescope(created_by=user, reviewer_decision=EquipmentItemReviewerDecision.APPROVED)
        topic = Generators.forum_topic(forum=telescope1.forum)

        client = APIClient()
        client.force_authenticate(user=moderator)

        client.post(
            reverse('astrobin_apps_equipment:telescope-detail', args=(telescope1.pk,)) + 'reject/', {
                'reason': EquipmentItemRejectionReason.DUPLICATE,
                'duplicate_of_klass': EquipmentItemKlass.TELESCOPE,
                'duplicate_of_usage_type': EquipmentItemUsageType.IMAGING,
                'duplicate_of': telescope2.id,
            }, format='json'
        )

        telescope2.refresh_from_db()
        self.assertEquals(topic, Topic.objects.filter(forum=telescope2.forum).first())

    @mock.patch('astrobin_apps_equipment.services.equipment_item_service.push_notification')
    def test_freeze_as_ambiguous_removes_from_presets(self, push_notification):
        from astrobin_apps_equipment.models import EquipmentPreset

        telescope = EquipmentGenerators.telescope()
        user = Generators.user()
        preset = EquipmentPreset.objects.create(user=user, name='Test')
        preset.imaging_telescopes.add(telescope)

        EquipmentItemService(telescope).freeze_as_ambiguous()

        self.assertFalse(EquipmentPreset.objects.filter(imaging_telescopes=telescope).exists())
        push_notification.assert_called_with([user], None, 'ambiguous-item-removed-from-presets', mock.ANY)

    def test_reject_as_duplicate_updates_marketplace_line_item(self):
        user = Generators.user()
        duplicate = EquipmentGenerators.telescope(created_by=user)
        telescope = EquipmentGenerators.telescope(created_by=user)

        listing = EquipmentGenerators.marketplace_listing()
        line_item = EquipmentGenerators.marketplace_line_item(listing=listing, item=duplicate)

        duplicate.reviewed_by = Generators.user()
        duplicate.reviewer_decision = EquipmentItemReviewerDecision.REJECTED
        duplicate.reviewer_rejection_reason = EquipmentItemRejectionReason.DUPLICATE
        duplicate.reviewer_rejection_duplicate_of_klass = EquipmentItemKlass.TELESCOPE
        duplicate.reviewer_rejection_duplicate_of = telescope.id

        EquipmentService.reject_item(duplicate)

        line_item.refresh_from_db()

        self.assertEquals(telescope, line_item.item_content_object)

    def test_reject_updates_marketplace_line_item(self):
        user = Generators.user()
        bad = EquipmentGenerators.telescope(created_by=user)

        listing = EquipmentGenerators.marketplace_listing()
        line_item = EquipmentGenerators.marketplace_line_item(listing=listing, item=bad)

        original_name = str(bad)

        bad.reviewed_by = Generators.user()
        bad.reviewer_decision = EquipmentItemReviewerDecision.REJECTED
        bad.reviewer_rejection_reason = EquipmentItemRejectionReason.OTHER

        EquipmentService.reject_item(bad)

        line_item.refresh_from_db()

        # Content type didn't change
        self.assertEquals(ContentType.objects.get_for_model(bad), line_item.item_content_type)

        # Item is now reverted to plain text version
        self.assertIsNone(line_item.item_object_id)
        self.assertIsNone(line_item.item_content_object)
        self.assertEquals(original_name, line_item.item_plain_text)
