from unittest.mock import patch

from django.core.cache import cache
from rest_framework.test import APITestCase

from astrobin.tests.generators import Generators
from astrobin_apps_premium.services.premium_service import SubscriptionName


class TestImageViewSet(APITestCase):
    def test_list_no_images(self):
        response = self.client.get('/api/v2/images/image/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("count"), 0)

    def test_list_has_deep_sky_acquisitions(self):
        image = Generators.image()
        response = self.client.get('/api/v2/images/image/?has-deepsky-acquisitions=true')

        self.assertEqual(response.status_code, 400)  # Bad request because there's no user

        response = self.client.get(f'/api/v2/images/image/?user={image.user.id}&has-deepsky-acquisitions=true')

        self.assertEqual(response.status_code, 403)  # I'm not the owner

        self.client.force_authenticate(user=image.user)

        response = self.client.get(f'/api/v2/images/image/?user={image.user.id}&has-deepsky-acquisitions=true')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("count"), 0)

        Generators.deep_sky_acquisition(image)

        response = self.client.get(f'/api/v2/images/image/?user={image.user.id}&has-deepsky-acquisitions=true')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("count"), 1)

    def test_list_has_solar_system_acquisitions(self):
        image = Generators.image()
        response = self.client.get('/api/v2/images/image/?has-solarsystem-acquisitions=true')

        self.assertEqual(response.status_code, 400)  # Bad request because there's no user

        response = self.client.get(f'/api/v2/images/image/?user={image.user.id}&has-solarsystem-acquisitions=true')

        self.assertEqual(response.status_code, 403)  # I'm not the owner

        self.client.force_authenticate(user=image.user)
        response = self.client.get(f'/api/v2/images/image/?user={image.user.id}&has-solarsystem-acquisitions=true')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("count"), 0)  # No acquisitions

        Generators.solar_system_acquisition(image)

        response = self.client.get(f'/api/v2/images/image/?user={image.user.id}&has-solarsystem-acquisitions=true')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("count"), 1)

    def test_list_public_image(self):
        image = Generators.image()
        response = self.client.get('/api/v2/images/image/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("count"), 1)
        self.assertEqual(response.data.get("results")[0].get("pk"), image.pk)

    def test_list_public_image_as_collaborator(self):
        image = Generators.image()
        collaborator = Generators.user()
        another_user = Generators.user()
        image.collaborators.add(collaborator)

        response = self.client.get('/api/v2/images/image/?user={}'.format(collaborator.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("count"), 1)

        response = self.client.get('/api/v2/images/image/?user={}'.format(image.user.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("count"), 1)

        response = self.client.get('/api/v2/images/image/?user={}'.format(another_user.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("count"), 0)

    def test_list_wip_image(self):
        Generators.image(is_wip=True)
        response = self.client.get('/api/v2/images/image/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("count"), 0)

    def test_list_including_wip_image_without_user(self):
        Generators.image(is_wip=True)
        response = self.client.get(f'/api/v2/images/image/?include-staging-area=true')
        self.assertEqual(response.status_code, 400)

    def test_list_including_wip_image_when_anon(self):
        image = Generators.image(is_wip=True)
        response = self.client.get(f'/api/v2/images/image/?include-staging-area=true&user={image.user.id}')
        self.assertEqual(response.status_code, 403)

    def test_list_including_wip_image_when_owner(self):
        image = Generators.image(is_wip=True)
        self.client.force_authenticate(user=image.user)
        response = self.client.get(f'/api/v2/images/image/?include-staging-area=true&user={image.user.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("count"), 1)
        self.assertEqual(response.data.get("results")[0].get("pk"), image.pk)

    def test_list_including_wip_image_when_not_owner(self):
        image = Generators.image(is_wip=True)
        self.client.force_authenticate(user=Generators.user())
        response = self.client.get(f'/api/v2/images/image/?include-staging-area=true&user={image.user.id}')
        self.assertEqual(response.status_code, 403)

    def test_retrieve_404(self):
        response = self.client.get('/api/v2/images/image/1/')
        self.assertEqual(response.status_code, 404)

    def test_retrieve_public_image(self):
        image = Generators.image()
        response = self.client.get(f'/api/v2/images/image/{image.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("pk"), image.pk)

    def test_retrieve_public_image_as_owner(self):
        image = Generators.image()
        self.client.force_authenticate(user=image.user)
        response = self.client.get(f'/api/v2/images/image/{image.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("pk"), image.pk)

    def test_retrieve_public_image_as_other_user(self):
        image = Generators.image()
        self.client.force_authenticate(user=Generators.user())
        response = self.client.get(f'/api/v2/images/image/{image.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("pk"), image.pk)

    def test_retrieve_wip_image_as_anon(self):
        # This should work because WIP images are unlisted, not private
        image = Generators.image(is_wip=True)
        response = self.client.get(f'/api/v2/images/image/{image.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("pk"), image.pk)

    def test_retrieve_wip_image_as_owner(self):
        image = Generators.image(is_wip=True)
        self.client.force_authenticate(user=image.user)
        response = self.client.get(f'/api/v2/images/image/{image.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("pk"), image.pk)

    def test_retrieve_wip_image_as_other_user(self):
        # This should work because WIP images are unlisted, not private
        image = Generators.image(is_wip=True)
        self.client.force_authenticate(user=Generators.user())
        response = self.client.get(f'/api/v2/images/image/{image.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("pk"), image.pk)

    def test_retrieve_public_image_by_hash(self):
        image = Generators.image()
        response = self.client.get(f'/api/v2/images/image/?hash={image.hash}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("results")[0].get("pk"), image.pk)

    def test_retrieve_public_image_by_hash_as_owner(self):
        image = Generators.image()
        self.client.force_authenticate(user=image.user)
        response = self.client.get(f'/api/v2/images/image/?hash={image.hash}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("results")[0].get("pk"), image.pk)

    def test_retrieve_public_image_by_hash_as_other_user(self):
        image = Generators.image()
        self.client.force_authenticate(user=Generators.user())
        response = self.client.get(f'/api/v2/images/image/?hash={image.hash}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("results")[0].get("pk"), image.pk)

    def test_retrieve_wip_image_by_hash_as_anon(self):
        # This should work because WIP images are unlisted, not private
        image = Generators.image(is_wip=True)
        response = self.client.get(f'/api/v2/images/image/?hash={image.hash}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("count"), 1)
        self.assertEqual(response.data.get("results")[0].get("pk"), image.pk)

    def test_retrieve_wip_image_by_hash_as_owner(self):
        image = Generators.image(is_wip=True)
        self.client.force_authenticate(user=image.user)
        response = self.client.get(f'/api/v2/images/image/?hash={image.hash}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("count"), 1)
        self.assertEqual(response.data.get("results")[0].get("pk"), image.pk)

    def test_retrieve_wip_image_by_hash_as_other_user(self):
        # This should work because WIP images are unlisted, not private
        image = Generators.image(is_wip=True)
        self.client.force_authenticate(user=Generators.user())
        response = self.client.get(f'/api/v2/images/image/?hash={image.hash}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("count"), 1)
        self.assertEqual(response.data.get("results")[0].get("pk"), image.pk)

    def test_list_only_staging_area_with_user(self):
        Generators.image()
        response = self.client.get('/api/v2/images/image/?only-staging-area=true')
        self.assertEqual(response.status_code, 400)

    def test_list_only_staging_area(self):
        image = Generators.image()
        self.client.force_authenticate(user=image.user)
        response = self.client.get(f'/api/v2/images/image/?only-staging-area=true&user={image.user.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("count"), 0)

        image.is_wip = True
        image.save()

        response = self.client.get(f'/api/v2/images/image/?only-staging-area=true&user={image.user.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("count"), 1)
        self.assertEqual(response.data.get("results")[0].get("pk"), image.pk)

    def test_list_only_staging_area_as_anon(self):
        image = Generators.image(is_wip=True)
        response = self.client.get(f'/api/v2/images/image/?only-staging-area=true&user={image.user.id}')
        self.assertEqual(response.status_code, 403)

    def test_list_only_staging_area_as_other_user(self):
        image = Generators.image(is_wip=True)
        self.client.force_authenticate(user=Generators.user())
        response = self.client.get(f'/api/v2/images/image/?only-staging-area=true&user={image.user.id}')
        self.assertEqual(response.status_code, 403)

    def test_list_by_user(self):
        image1 = Generators.image()
        Generators.image()
        response = self.client.get(f'/api/v2/images/image/?user={image1.user.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("count"), 1)
        self.assertEqual(response.data.get("results")[0].get("pk"), image1.pk)

    def test_list_by_user_and_year(self):
        image1 = Generators.image()
        Generators.image()  # Image from another user will not be included.

        response = self.client.get(f'/api/v2/images/image/?user={image1.user.id}&subsection=year')
        self.assertEqual(response.status_code, 200)

        # Nothing in the menu as there is no acquisition.
        self.assertEqual(response.data.get("menu"), [('0', 'No date specified')])
        # The image is still there but UI won't use it.
        self.assertEqual(response.data.get("count"), 1)
        self.assertEqual(response.data.get("results")[0].get("pk"), image1.pk)

        response = self.client.get(f'/api/v2/images/image/?user={image1.user.id}&subsection=year&active=1920')
        self.assertEqual(response.status_code, 200)

        # Nothing in the menu as there is no acquisition.
        self.assertEqual(response.data.get("menu"), [('0', 'No date specified')])
        # No images in 1920.
        self.assertEqual(response.data.get("count"), 0)

        Generators.deep_sky_acquisition(image1, date="1920-01-01")

        response = self.client.get(f'/api/v2/images/image/?user={image1.user.id}&subsection=year')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("menu"), [('1920', '1920'), ('0', 'No date specified')])
        self.assertEqual(response.data.get("results")[0].get("pk"), image1.pk)

        response = self.client.get(f'/api/v2/images/image/?user={image1.user.id}&subsection=year&active=1920')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("menu"), [('1920', '1920'), ('0', 'No date specified')])
        self.assertEqual(response.data.get("count"), 1)
        self.assertEqual(response.data.get("results")[0].get("pk"), image1.pk)

        response = self.client.get(f'/api/v2/images/image/?user={image1.user.id}&subsection=year&active=1921')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("menu"), [('1920', '1920'), ('0', 'No date specified')])
        self.assertEqual(response.data.get("count"), 0)

    def test_list_by_user_and_collection(self):
        image1 = Generators.image()
        Generators.image()  # Another image will not be included
        collection = Generators.collection()
        image1.collections.add(collection)

        response = self.client.get(f'/api/v2/images/image/?user={image1.user.id}&collection={collection.pk}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("count"), 1)
        self.assertEqual(response.data.get("results")[0].get("pk"), image1.pk)

    def test_list_by_user_and_collection_with_order_by_tag(self):
        user = Generators.user()
        image1 = Generators.image(user=user)
        image2 = Generators.image(user=user)
        kv1 = Generators.key_value_tag(key="a", value=1, image=image1)
        kv2 = Generators.key_value_tag(key="a", value=2, image=image2)
        collection = Generators.collection(order_by_tag="a")
        collection.images.add(image1)
        collection.images.add(image2)

        response = self.client.get(f'/api/v2/images/image/?user={image1.user.id}&collection={collection.pk}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("count"), 2)
        self.assertEqual(response.data.get("results")[0].get("pk"), image1.pk)
        self.assertEqual(response.data.get("results")[1].get("pk"), image2.pk)

        kv1.value = 2
        kv1.save()

        kv2.value = 1
        kv2.save()

        response = self.client.get(f'/api/v2/images/image/?user={image1.user.id}&collection={collection.pk}')

        # Images will be inverted
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("count"), 2)
        self.assertEqual(response.data.get("results")[0].get("pk"), image2.pk)
        self.assertEqual(response.data.get("results")[1].get("pk"), image1.pk)

    def test_undelete_by_anonymous(self):
        image = Generators.image()
        image.delete()
        response = self.client.post(f'/api/v2/images/image/{image.pk}/undelete/')
        self.assertEqual(response.status_code, 401)

    def test_undelete_by_non_owner(self):
        image = Generators.image()
        image.delete()
        self.client.force_authenticate(user=Generators.user())
        response = self.client.patch(f'/api/v2/images/image/{image.pk}/undelete/')
        self.assertEqual(response.status_code, 403)

    def test_undelete_by_owner_non_ultimate(self):
        image = Generators.image()
        image.delete()
        self.client.force_authenticate(user=Generators.user())
        response = self.client.patch(f'/api/v2/images/image/{image.pk}/undelete/')
        self.assertEqual(response.status_code, 403)

    def test_undelete_by_owner(self):
        image = Generators.image()
        image.delete()
        Generators.premium_subscription(image.user, SubscriptionName.ULTIMATE_2020)
        self.client.force_authenticate(user=image.user)
        response = self.client.patch(f'/api/v2/images/image/{image.pk}/undelete/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data.get("deleted"))
        
    def test_retrieve_image_by_pk_with_country_specific_cache(self):
        # Clear cache before testing
        cache.clear()
        
        image = Generators.image()
        
        # Mock the get_client_country_code function to return a specific country
        with patch('astrobin.utils.get_client_country_code') as mock_country_code:
            mock_country_code.return_value = 'US'
            
            # First request should not be cached
            response1 = self.client.get(f'/api/v2/images/image/{image.pk}/')
            self.assertEqual(response1.status_code, 200)
            
            # Second request should be served from cache
            response2 = self.client.get(f'/api/v2/images/image/{image.pk}/')
            self.assertEqual(response2.status_code, 200)
            
            # The mock should have been called twice
            self.assertEqual(mock_country_code.call_count, 2)
            
            # Change the mocked country code
            mock_country_code.return_value = 'IT'
            
            # This request should not be cached because the country is different
            response3 = self.client.get(f'/api/v2/images/image/{image.pk}/')
            self.assertEqual(response3.status_code, 200)
            
            # Mock should now have been called 3 times
            self.assertEqual(mock_country_code.call_count, 3)
            
            # Another request with the same country should be cached
            response4 = self.client.get(f'/api/v2/images/image/{image.pk}/')
            self.assertEqual(response4.status_code, 200)
            
            # Mock should now have been called 4 times
            self.assertEqual(mock_country_code.call_count, 4)
        
    def test_retrieve_image_by_hash_with_country_specific_cache(self):
        # Clear cache before testing
        cache.clear()
        
        image = Generators.image()
        
        # Mock the get_client_country_code function to return a specific country
        with patch('astrobin.utils.get_client_country_code') as mock_country_code:
            mock_country_code.return_value = 'US'
            
            # First request should not be cached
            response1 = self.client.get(f'/api/v2/images/image/?hash={image.hash}')
            self.assertEqual(response1.status_code, 200)
            
            # Second request should be served from cache
            response2 = self.client.get(f'/api/v2/images/image/?hash={image.hash}')
            self.assertEqual(response2.status_code, 200)
            
            # The mock should have been called twice
            self.assertEqual(mock_country_code.call_count, 2)
            
            # Change the mocked country code
            mock_country_code.return_value = 'IT'
            
            # This request should not be cached because the country is different
            response3 = self.client.get(f'/api/v2/images/image/?hash={image.hash}')
            self.assertEqual(response3.status_code, 200)
            
            # Mock should now have been called 3 times
            self.assertEqual(mock_country_code.call_count, 3)
            
            # Another request with the same country should be cached
            response4 = self.client.get(f'/api/v2/images/image/?hash={image.hash}')
            self.assertEqual(response4.status_code, 200)
            
            # Mock should now have been called 4 times
            self.assertEqual(mock_country_code.call_count, 4)
