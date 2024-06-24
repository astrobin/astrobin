from unittest.mock import patch

from django.urls import reverse
from rest_framework.test import APITestCase

from astrobin.tests.generators import Generators
from astrobin_apps_equipment.api.permissions.may_access_marketplace import MayAccessMarketplace
from astrobin_apps_equipment.models import EquipmentItemMarketplaceOffer
from astrobin_apps_equipment.models.equipment_item_marketplace_offer import EquipmentItemMarketplaceOfferStatus
from astrobin_apps_equipment.tests.equipment_generators import EquipmentGenerators


class EquipmentItemMarketplaceListingViewSetTestCase(APITestCase):
    def setUp(self):
        # Patch the has_permission and has_object_permission methods
        self.may_access_marketplace_permission_patcher = patch.object(
            MayAccessMarketplace, 'has_permission', return_value=True
        )
        self.may_access_marketplace_permission_patcher.start()

        self.may_access_marketplace_object_permission_patcher = patch.object(
            MayAccessMarketplace, 'has_object_permission', return_value=True
        )
        self.may_access_marketplace_object_permission_patcher.start()

    def tearDown(self):
        self.may_access_marketplace_permission_patcher.stop()
        self.may_access_marketplace_object_permission_patcher.stop()

    def test_multiple_accepted_offers_for_the_same_lineitem_not_allowed(self):
        seller = Generators.user()
        listing = EquipmentGenerators.marketplace_listing(user=seller)
        line_item = EquipmentGenerators.marketplace_line_item(listing=listing, user=seller)

        buyer_1 = Generators.user()
        buyer_2 = Generators.user()

        offer_1 = EquipmentGenerators.marketplace_offer(
            listing=listing,
            line_item=line_item,
            user=buyer_1,
            status=EquipmentItemMarketplaceOfferStatus.ACCEPTED
        )
        offer_2 = EquipmentGenerators.marketplace_offer(
            listing=listing,
            line_item=line_item,
            user=buyer_2,
            status=EquipmentItemMarketplaceOfferStatus.PENDING
        )

        self.client.login(username=seller.username, password='password')

        url = reverse('astrobin_apps_equipment:marketplace-offer-detail', kwargs={
            'listing_id': listing.pk,
            'line_item_id': line_item.pk,
            'pk': offer_1.pk
        }) + 'accept/'

        response = self.client.put(url, {}, format='json')

        self.assertEqual(response.status_code, 200)
        line_item.refresh_from_db()
        self.assertEqual(line_item.reserved_to, buyer_1)
        self.assertIsNotNone(line_item.reserved)

        url = reverse('astrobin_apps_equipment:marketplace-offer-detail', kwargs={
            'listing_id': listing.pk,
            'line_item_id': line_item.pk,
            'pk': offer_2.pk
        }) + 'accept/'

        response = self.client.put(url, {}, format='json')

        self.assertEqual(response.status_code, 400)
        line_item.refresh_from_db()
        self.assertEqual(line_item.reserved_to, buyer_1)
        self.assertIsNotNone(line_item.reserved)


