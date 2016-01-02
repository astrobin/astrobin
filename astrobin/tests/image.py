# Django
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

class ImageTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'test', 'test@test.com', 'password')

    def tearDown(self):
        self.user.delete()

    def test_upload(self):
        self.client.login(username = 'test', password = 'password')

        # Test file with invalid extension
        f = open('astrobin/fixtures/invalid_file', 'rb')
        response = self.client.post(
            reverse('image_upload_process'),
            {'image_file': f},
            follow = True)
        self.assertRedirects(
            response,
            reverse('image_upload'),
            status_code = 302,
            target_status_code = 200)
        import pdb; pdb.set_trace()
        message = self.user.get_messages()[0]
        self.assertEqual(message.tags, "error")
        self.assertTrue("Invalid image" in message.message)

        # Test that the image goes thru.
        f = open('astrobin/fixtures/test.jpg', 'rb')
        response = self.client.post(
            reverse('image_upload_process'),
            {'image_file': f},
            follow = True)
        self.assertRedirects(
            response,
            reverse('image_edit_watermark', kwargs = {'id': 1}),
            status_code = 302,
            target_status_code = 200)

