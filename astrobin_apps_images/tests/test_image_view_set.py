from rest_framework.test import APITestCase

from astrobin.tests.generators import Generators


class TestImageViewSet(APITestCase):
    def test_list_no_images(self):
        response = self.client.get('/api/v2/images/image/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("count"), 0)

    def test_list_public_image(self):
        image = Generators.image()
        response = self.client.get('/api/v2/images/image/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("count"), 1)
        self.assertEqual(response.data.get("results")[0].get("pk"), image.pk)

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
        self.assertEqual(response.data.get("results")[0].get("pk"), image.pk)

    def test_retrieve_wip_image_by_hash_as_owner(self):
        image = Generators.image(is_wip=True)
        self.client.force_authenticate(user=image.user)
        response = self.client.get(f'/api/v2/images/image/?hash={image.hash}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("results")[0].get("pk"), image.pk)

    def test_retrieve_wip_image_by_hash_as_other_user(self):
        # This should work because WIP images are unlisted, not private
        image = Generators.image(is_wip=True)
        self.client.force_authenticate(user=Generators.user())
        response = self.client.get(f'/api/v2/images/image/?hash={image.hash}')
        self.assertEqual(response.status_code, 200)
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
