import simplejson as json

from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.test import TestCase

from astrobin.tests.generators import Generators


class CommonTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'user', 'user@test.com', 'password')

    def tearDown(self):
        self.user.delete()

    def test_real_name_in_user_api(self):
        """
        Tests the userprofile.real_name field is available in the user api.
        """
        self.user.userprofile.real_name = 'Real Name'
        self.user.userprofile.save(keep_deleted=True)

        self.client.login(username='user', password='password')

        response = json.loads(self.client.get(
            reverse_lazy('user-detail', args=(self.user.pk,))).content)
        self.assertTrue('userprofile' in response)
        self.assertEqual(self.user.userprofile.pk, response['userprofile'])

        response = json.loads(self.client.get(
            reverse_lazy('userprofile-detail', args=(self.user.userprofile.pk,))).content)
        self.assertTrue('real_name' in response)
        self.assertEqual('Real Name', response['real_name'])

    def test_change_gallery_header_unauthenticated(self):
        """
        Tests that an unauthenticated user cannot change the gallery header.
        """
        response = self.client.put(
            reverse_lazy('userprofile-change-gallery-header', args=(self.user.userprofile.pk, 'image_id',))
        )
        self.assertEqual(response.status_code, 401)

    def test_change_gallery_header_another_user(self):
        """
        Tests that a user cannot change another user's gallery header.
        """
        other_user = Generators.user()
        user = Generators.user()

        self.client.force_login(user)

        response = self.client.put(
            reverse_lazy('userprofile-change-gallery-header', args=(other_user.userprofile.pk, 'image_id',))
        )
        self.assertEqual(response.status_code, 403)

    def test_change_gallery_header_another_users_image(self):
        """
        Tests that a user cannot change gallery header using another user's image.
        """
        other_user = Generators.user()
        image = Generators.image(user=other_user)
        user = Generators.user()

        self.client.force_login(user)

        response = self.client.put(
            reverse_lazy('userprofile-change-gallery-header', args=(user.userprofile.pk, image.hash,))
        )
        self.assertEqual(response.status_code, 403)

    def test_change_gallery_header(self):
        """
        Tests that a user can change their own gallery header.
        """
        user = Generators.user()
        image = Generators.image(user=user)
        thumbnail = image.thumbnail('hd', None, sync=True)

        self.client.force_login(user)

        response = self.client.put(
            reverse_lazy('userprofile-change-gallery-header', args=(user.userprofile.pk, image.hash,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(user.userprofile.gallery_header_image, thumbnail)
