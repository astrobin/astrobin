from datetime import timedelta

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from astrobin_apps_equipment.tests.equipment_generators import EquipmentGenerators
from astrobin_apps_equipment.types.marketplace_line_item_condition import MarketplaceLineItemCondition
from common.services import DateTimeService


class EquipmentItemMarketplaceListingViewSetTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.other_user = User.objects.create_user(username='testuser2', password='testpassword')

        self.client.login(username='testuser', password='testpassword')

        telescope = EquipmentGenerators.telescope()

        self.listing = EquipmentGenerators.marketplace_listing(
            user=self.user,
            expiration=DateTimeService.now() + timedelta(days=1)
        )

        self.line_item = EquipmentGenerators.marketplace_line_item(
            listing=self.listing,
            item=telescope
        )

    def test_list_view_excludes_expired_listings(self):
        url = reverse('astrobin_apps_equipment:marketplace-listing-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        self.listing.expiration = DateTimeService.now() - timedelta(days=1)
        self.listing.save()

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_list_view_includes_expired_listings_for_authenticated_user(self):
        url = reverse('astrobin_apps_equipment:marketplace-listing-list')
        self.listing.expiration = DateTimeService.now() - timedelta(days=1)
        self.listing.save()

        response = self.client.get(url, {'expired': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_list_view_excludes_expired_listings_for_unauthenticated_user(self):
        url = reverse('astrobin_apps_equipment:marketplace-listing-list')
        self.listing.expiration = DateTimeService.now() - timedelta(days=1)
        self.listing.save()

        self.client.logout()
        response = self.client.get(url, {'expired': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_retrieve_view_allows_expired_listing_for_owner(self):
        url = reverse('astrobin_apps_equipment:marketplace-listing-detail', args=[self.listing.pk,])
        self.listing.expiration = DateTimeService.now() - timedelta(days=1)
        self.listing.save()

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.listing.pk)

    def test_retrieve_view_disallows_expired_listing_for_non_owner(self):
        url = reverse('astrobin_apps_equipment:marketplace-listing-detail', args=[self.listing.pk,])
        self.listing.expiration = DateTimeService.now() - timedelta(days=1)
        self.listing.save()

        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_view_disallows_expired_listing_for_different_authenticated_user(self):
        other_user = User.objects.create_user(username='otheruser', password='otherpassword')
        self.client.login(username='otheruser', password='otherpassword')

        url = reverse('astrobin_apps_equipment:marketplace-listing-detail', args=[self.listing.pk,])
        self.listing.expiration = DateTimeService.now() - timedelta(days=1)
        self.listing.save()

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_filter_by_min_price(self):
        url = reverse('astrobin_apps_equipment:marketplace-listing-list')
        self.listing.price_chf = 500
        self.listing.save()

        response = self.client.get(url, {'min_price': 400})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        listings = response.data.get('results', [])
        self.assertTrue(any(listing['id'] == self.listing.pk for listing in listings))

    def test_filter_by_max_price(self):
        url = reverse('astrobin_apps_equipment:marketplace-listing-list')
        self.listing.price_chf = 300
        self.listing.save()

        response = self.client.get(url, {'max_price': 400})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        listings = response.data.get('results', [])
        self.assertTrue(any(listing['id'] == self.listing.pk for listing in listings))

    def test_filter_by_region(self):
        url = reverse('astrobin_apps_equipment:marketplace-listing-list')
        self.listing.country = 'US'
        self.listing.save()

        response = self.client.get(url, {'region': 'US'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        listings = response.data.get('results', [])
        self.assertTrue(any(listing['id'] == self.listing.pk for listing in listings))

    def test_invalid_query_parameters(self):
        url = reverse('astrobin_apps_equipment:marketplace-listing-list')
        response = self.client.get(url, {'invalid_param': 'invalid_value'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_expired_false_excludes_expired_listings(self):
        url = reverse('astrobin_apps_equipment:marketplace-listing-list')
        self.listing.expiration = DateTimeService.now() - timedelta(days=1)
        self.listing.save()

        response = self.client.get(url, {'expired': 'false'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        listings = response.data.get('results', [])
        self.assertFalse(any(listing['id'] == self.listing.pk for listing in listings))

    def test_listing_does_not_exist(self):
        url = reverse('astrobin_apps_equipment:marketplace-listing-detail', args=[99999, ])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_filter_line_items_offers_by_user(self):
        url = reverse('astrobin_apps_equipment:marketplace-listing-list')
        user_id = self.other_user.id
        self.line_item.offers.create(user_id=user_id, listing_id=self.listing.id)

        response = self.client.get(url, {'offers_by_user': user_id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(item['id'] == self.listing.pk for item in response.data['results']))

    def test_filter_line_items_by_sold_status(self):
        url = reverse('astrobin_apps_equipment:marketplace-listing-list')
        self.line_item.sold = DateTimeService.now()
        self.line_item.save()

        response = self.client.get(url, {'sold': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(item['id'] == self.listing.pk for item in response.data['results']))

    def test_filter_line_items_by_item_type(self):
        url = reverse('astrobin_apps_equipment:marketplace-listing-list')
        item_type = 'telescope'
        self.line_item.item_type = item_type
        self.line_item.save()

        response = self.client.get(url, {'item_type': item_type})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(item['id'] == self.listing.pk for item in response.data['results']))

    def test_filter_line_items_by_price(self):
        url = reverse('astrobin_apps_equipment:marketplace-listing-list')
        self.line_item.price_chf = 500
        self.line_item.save()

        response = self.client.get(url, {'min_price': 400, 'max_price': 600})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(item['id'] == self.listing.pk for item in response.data['results']))

    def test_filter_line_items_by_condition(self):
        url = reverse('astrobin_apps_equipment:marketplace-listing-list')
        condition = MarketplaceLineItemCondition.NEW.value
        self.line_item.condition = condition
        self.line_item.save()

        response = self.client.get(url, {'condition': condition})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(item['id'] == self.listing.pk for item in response.data['results']))

    def test_filter_line_items_by_query(self):
        url = reverse('astrobin_apps_equipment:marketplace-listing-list')
        query = 'specific query'
        self.line_item.item_name = 'Item matching specific query'
        self.line_item.save()

        response = self.client.get(url, {'query': query})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(item['id'] == self.listing.pk for item in response.data['results']))

    def test_fetch_own_expired_listing_by_hash(self):
        self.client.login(username='testuser', password='testpassword')  # Ensure the user is logged in

        # Create an expired listing with a specific hash for the test user
        expired_listing = EquipmentGenerators.marketplace_listing(
            user=self.user,
            expiration=DateTimeService.now() - timedelta(days=1),
        )
        EquipmentGenerators.marketplace_line_item(listing=expired_listing)

        # User tries to fetch their own expired listing by hash
        url = reverse('astrobin_apps_equipment:marketplace-listing-list')
        response = self.client.get(url, {'hash': expired_listing.hash})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if the listing with the specified hash is in the results
        found = any(listing['hash'] == expired_listing.hash for listing in response.data['results'])
        self.assertTrue(found, "Expired listing with the specified hash was not found for the owner")

    def test_different_user_cannot_fetch_expired_listing_by_hash(self):
        url = reverse('astrobin_apps_equipment:marketplace-listing-list')
        # Create an expired listing for the test user
        expired_listing = EquipmentGenerators.marketplace_listing(
            user=self.user,
            expiration=DateTimeService.now() - timedelta(days=1),
        )
        EquipmentGenerators.marketplace_line_item(listing=expired_listing)

        # Different user tries to fetch the test user's expired listing by hash
        self.client.logout()
        self.client.login(username='testuser2', password='testpassword')
        response = self.client.get(url, {'hash': expired_listing.hash})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(any(listing['id'] == expired_listing.pk for listing in response.data['results']))
