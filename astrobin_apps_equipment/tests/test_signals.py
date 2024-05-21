from django.test import TestCase
from mock import mock
from mock.mock import patch

from astrobin.tests.generators import Generators
from astrobin_apps_equipment.models import Camera, EquipmentItemMarketplaceMasterOffer
from astrobin_apps_equipment.models.equipment_item import EquipmentItemReviewerDecision
from astrobin_apps_equipment.models.equipment_item_marketplace_offer import EquipmentItemMarketplaceOfferStatus
from astrobin_apps_equipment.tests.equipment_generators import EquipmentGenerators
from astrobin_apps_groups.models import Group
from common.constants import GroupName
from common.services import DateTimeService


class SignalsTest(TestCase):
    def test_mirror_modified_camera(self):
        camera = EquipmentGenerators.camera()
        modified = EquipmentGenerators.camera(
            created_by=camera.created_by,
            brand=camera.brand,
            name=camera.name,
            image=camera.image,
            type=camera.type,
            sensor=camera.sensor,
            cooled=camera.cooled,
            max_cooling=camera.max_cooling,
            back_focus=camera.back_focus,
            modified=True,
        )

        camera.name = camera.name + ' updated'
        camera.save()

        modified = Camera.objects.get(pk=modified.pk)

        self.assertEqual(camera.name, modified.name)

    def test_mirror_modified_camera_deletion(self):
        camera = EquipmentGenerators.camera()
        modified = EquipmentGenerators.camera(
            created_by=camera.created_by,
            brand=camera.brand,
            name=camera.name,
            image=camera.image,
            type=camera.type,
            sensor=camera.sensor,
            cooled=camera.cooled,
            max_cooling=camera.max_cooling,
            back_focus=camera.back_focus,
            modified=True,
        )

        camera.delete()

        self.assertFalse(Camera.objects.filter(pk=modified.pk).exists())

    def test_remove_sensor_from_cameras_after_deletion(self):
        camera = EquipmentGenerators.camera()
        camera.sensor.delete()
        camera = Camera.objects.get(pk=camera.pk)

        self.assertIsNone(camera.sensor)

    def test_forum_creation(self):
        telescope = EquipmentGenerators.telescope()
        self.assertIsNone(telescope.forum)

        telescope.reviewer_decision = EquipmentItemReviewerDecision.APPROVED
        telescope.save()
        telescope.refresh_from_db()

        self.assertIsNotNone(telescope.forum)

    def test_forum_deletion(self):
        telescope = EquipmentGenerators.telescope(reviewer_decision=EquipmentItemReviewerDecision.APPROVED)
        self.assertIsNotNone(telescope.forum)

        telescope.reviewer_decision = EquipmentItemReviewerDecision.REJECTED
        telescope.save()
        telescope.refresh_from_db()

        self.assertIsNone(telescope.forum)

    @patch('astrobin_apps_equipment.tasks.push_notification')
    def test_marketplace_master_offer_created(self, push_notification):
        seller = Generators.user()
        listing = EquipmentGenerators.marketplace_listing(user=seller)
        line_item_1 = EquipmentGenerators.marketplace_line_item(listing=listing, user=seller)
        line_item_2 = EquipmentGenerators.marketplace_line_item(listing=listing, user=seller)
        buyer = Generators.user()
        offer_1 = EquipmentGenerators.marketplace_offer(listing=listing, line_item=line_item_1, user=buyer)
        offer_2 = EquipmentGenerators.marketplace_offer(listing=listing, line_item=line_item_2, user=buyer)

        self.assertEqual(1, EquipmentItemMarketplaceMasterOffer.objects.filter(offers=offer_1).count())
        self.assertEqual(1, EquipmentItemMarketplaceMasterOffer.objects.filter(offers=offer_2).count())

        push_notification.assert_called_with([seller], buyer, 'marketplace-offer-created', mock.ANY)

        # Two offers created still results in one notification.
        push_notification.asset_called_once()

    @patch('astrobin_apps_equipment.tasks.push_notification')
    def test_marketplace_master_offer_deleted(self, push_notification):
        seller = Generators.user()
        listing = EquipmentGenerators.marketplace_listing(user=seller)
        line_item_1 = EquipmentGenerators.marketplace_line_item(listing=listing, user=seller)
        line_item_2 = EquipmentGenerators.marketplace_line_item(listing=listing, user=seller)
        buyer = Generators.user()
        offer_1 = EquipmentGenerators.marketplace_offer(listing=listing, line_item=line_item_1, user=buyer)
        offer_2 = EquipmentGenerators.marketplace_offer(listing=listing, line_item=line_item_2, user=buyer)

        push_notification.reset_mock()

        offer_1.delete()
        offer_2.delete()

        self.assertEqual(0, EquipmentItemMarketplaceMasterOffer.objects.filter(offers=offer_1).count())
        self.assertEqual(0, EquipmentItemMarketplaceMasterOffer.objects.filter(offers=offer_2).count())

        push_notification.assert_called_with([seller], buyer, 'marketplace-offer-retracted', mock.ANY)

        # Two offers deleted still results in one notification.
        push_notification.asset_called_once()

    @patch('astrobin_apps_equipment.tasks.push_notification')
    def test_marketplace_offers_updated(self, push_notification):
        seller = Generators.user()
        listing = EquipmentGenerators.marketplace_listing(user=seller)
        line_item_1 = EquipmentGenerators.marketplace_line_item(listing=listing, user=seller)
        line_item_2 = EquipmentGenerators.marketplace_line_item(listing=listing, user=seller)
        buyer = Generators.user()
        offer_1 = EquipmentGenerators.marketplace_offer(listing=listing, line_item=line_item_1, user=buyer)
        offer_2 = EquipmentGenerators.marketplace_offer(listing=listing, line_item=line_item_2, user=buyer)

        push_notification.reset_mock()

        offer_1.amount += 1
        offer_2.amount += 1

        offer_1.save()
        offer_2.save()

        push_notification.assert_has_calls([
            mock.call([seller], buyer, 'marketplace-offer-updated', mock.ANY),
            mock.call([seller], buyer, 'marketplace-offer-updated', mock.ANY),
        ], any_order=True)

        push_notification.asset_called_times(2)

    @patch('astrobin_apps_equipment.tasks.push_notification')
    def test_marketplace_master_offer_accepted(self, push_notification):
        seller = Generators.user()
        listing = EquipmentGenerators.marketplace_listing(user=seller)
        line_item_1 = EquipmentGenerators.marketplace_line_item(listing=listing, user=seller)
        line_item_2 = EquipmentGenerators.marketplace_line_item(listing=listing, user=seller)
        buyer = Generators.user()
        offer_1 = EquipmentGenerators.marketplace_offer(listing=listing, line_item=line_item_1, user=buyer)
        offer_2 = EquipmentGenerators.marketplace_offer(listing=listing, line_item=line_item_2, user=buyer)

        push_notification.reset_mock()

        offer_1.status = EquipmentItemMarketplaceOfferStatus.ACCEPTED.value
        offer_2.status = EquipmentItemMarketplaceOfferStatus.ACCEPTED.value

        offer_1.save()
        offer_2.save()

        push_notification.assert_has_calls([
            mock.call([buyer], seller, 'marketplace-offer-accepted-by-seller', mock.ANY),
            mock.call([seller], None, 'marketplace-offer-accepted-by-you', mock.ANY),
        ], any_order=True)

        push_notification.asset_called_times(2)

    @patch('astrobin_apps_equipment.signals.push_notification')
    def test_marketplace_listing_updated(self, push_notification):
        seller = Generators.user()
        listing = EquipmentGenerators.marketplace_listing(user=seller)

        listing.title = 'title2'
        listing.save()

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(mock.ANY, listing.user, 'marketplace-listing-updated', mock.ANY)

        offer = EquipmentGenerators.marketplace_offer(listing=listing, user=seller)

        push_notification.reset_mock()

        listing.title = 'title3'
        listing.save()

        push_notification.assert_called_with([offer.user], listing.user, 'marketplace-listing-updated', mock.ANY)

        follower = Generators.user()
        Generators.follow(listing, user=follower)

        listing.title = 'title4'
        listing.save()

        push_notification.assert_called_with([seller, follower], listing.user, 'marketplace-listing-updated', mock.ANY)

    @patch('astrobin_apps_equipment.signals.push_notification')
    def test_marketplace_listing_deleted_no_followers(self, push_notification):
        seller = Generators.user()
        listing = EquipmentGenerators.marketplace_listing(user=seller)

        listing.delete()

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(mock.ANY, listing.user, 'marketplace-listing-deleted', mock.ANY)

    @patch('astrobin_apps_equipment.signals.push_notification')
    def test_marketplace_listing_deleted(self, push_notification):
        seller = Generators.user()
        listing = EquipmentGenerators.marketplace_listing(user=seller)

        offer = EquipmentGenerators.marketplace_offer(listing=listing, user=seller)
        follower = Generators.user()
        Generators.follow(listing, user=follower)

        listing.delete()

        push_notification.assert_called_with(
            [offer.user, follower], listing.user, 'marketplace-listing-deleted', mock.ANY
        )

    @patch('astrobin_apps_equipment.signals.push_notification')
    def test_marketplace_listing_sold_notification_not_sent(self, push_notification):
        seller = Generators.user()
        listing = EquipmentGenerators.marketplace_listing(user=seller)
        line_item = EquipmentGenerators.marketplace_line_item(listing=listing, user=seller)
        buyer = Generators.user()
        offer = EquipmentGenerators.marketplace_offer(
            listing=listing, line_item=line_item, user=buyer, status=EquipmentItemMarketplaceOfferStatus.ACCEPTED.value
        )

        line_item.sold = offer.created
        line_item.sold_to = buyer
        line_item.save()

        # Notification not sent because the buyer and the seller get notifications about accepted offers. The line item
        # sold notification is for followers and other offering users..

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(
                mock.ANY, seller, 'marketplace-listing-line-item-sold', mock.ANY
            )

    @patch('astrobin_apps_equipment.signals.push_notification')
    def test_marketplace_listing_sold_notification_sent(self, push_notification):
        seller = Generators.user()
        listing = EquipmentGenerators.marketplace_listing(user=seller)
        line_item = EquipmentGenerators.marketplace_line_item(listing=listing, user=seller)

        buyer1 = Generators.user()
        offer1 = EquipmentGenerators.marketplace_offer(
            listing=listing, line_item=line_item, user=buyer1, status=EquipmentItemMarketplaceOfferStatus.ACCEPTED.value
        )

        buyer2 = Generators.user()
        EquipmentGenerators.marketplace_offer(
            listing=listing, line_item=line_item, user=buyer2, status=EquipmentItemMarketplaceOfferStatus.PENDING.value
        )

        follower = Generators.user()
        Generators.follow(listing, user=follower)

        line_item.sold = offer1.created
        line_item.sold_to = buyer1
        line_item.save()

        # Notification not sent because the buyer and the seller get notifications about accepted offers. The line item
        # sold notification is for followers and other offering users..

        push_notification.assert_called_with(
            [buyer2, follower], seller, 'marketplace-listing-line-item-sold', mock.ANY
        )

    @patch('astrobin_apps_equipment.signals.push_notification')
    def test_marketplace_listing_by_user_you_follow_notification(self, push_notification):
        seller = Generators.user()
        listing = EquipmentGenerators.marketplace_listing(user=seller)
        follower = Generators.user()
        Generators.follow(seller, user=follower)
        group = Group.objects.create(
            name=GroupName.BETA_TESTERS,
            owner=follower,
            creator=follower,
        )
        group.members.add(follower)

        listing.approved = DateTimeService.now()
        listing.save()

        push_notification.assert_called_with([follower], seller, 'marketplace-listing-by-user-you-follow', mock.ANY)

    @patch('astrobin_apps_equipment.signals.push_notification')
    def test_marketplace_listing_by_user_you_follow_notification_no_followers(self, push_notification):
        seller = Generators.user()
        listing = EquipmentGenerators.marketplace_listing(user=seller)

        listing.approved = DateTimeService.now()
        listing.save()

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(mock.ANY, seller, 'marketplace-listing-by-user-you-follow', mock.ANY)

    @patch('astrobin_apps_equipment.signals.push_notification')
    def test_marketplace_listing_for_item_you_follow_notification(self, push_notification):
        seller = Generators.user()
        listing = EquipmentGenerators.marketplace_listing(user=seller)
        line_item = EquipmentGenerators.marketplace_line_item(listing=listing, user=seller)
        follower = Generators.user()
        Generators.follow(line_item.item_content_object, user=follower)
        group = Group.objects.create(
            name=GroupName.BETA_TESTERS,
            owner=follower,
            creator=follower,
        )
        group.members.add(follower)

        listing.approved = DateTimeService.now()
        listing.save()

        push_notification.assert_called_with([follower], seller, 'marketplace-listing-for-item-you-follow', mock.ANY)
