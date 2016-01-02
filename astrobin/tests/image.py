# Django
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

# AstroBin
from astrobin.models import Image

class ImageTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'test', 'test@test.com', 'password')

    def tearDown(self):
        self.user.delete()

    def _do_upload(self, filename):
        return self.client.post(
            reverse('image_upload_process'),
            {'image_file': open(filename, 'rb')},
            follow = True)

    def _assert_message(self, response, tags, content):
        storage = response.context[0]['messages']
        for message in storage:
            self.assertEqual(message.tags, tags)
            self.assertTrue(content in message.message)

    def test_upload(self):
        self.client.login(username = 'test', password = 'password')

        # Test file with invalid extension
        response = self._do_upload('astrobin/fixtures/invalid_file')
        self.assertRedirects(
            response,
            reverse('image_upload'),
            status_code = 302,
            target_status_code = 200)
        self._assert_message(response, "error unread", "Invalid image")

        # Test file with invalid content
        response = self._do_upload('astrobin/fixtures/invalid_file.jpg')
        self.assertRedirects(
            response,
            reverse('image_upload'),
            status_code = 302,
            target_status_code = 200)
        self._assert_message(response, "error unread", "Invalid image")

        # Test successful upload
        response = self._do_upload('astrobin/fixtures/test.jpg')
        self.assertRedirects(
            response,
            reverse('image_edit_watermark', kwargs = {'id': 1}),
            status_code = 302,
            target_status_code = 200)

        image = Image.objects.get(pk = 1)
        self.assertEqual(image.title, u"")

        # Test watermark
        response = self.client.post(
            reverse('image_edit_save_watermark'),
            {
                'image_id': 1,
                'watermark': True,
                'watermark_text': "Watermark test",
                'watermark_position': 0,
                'watermark_opacity': 100
            },
            follow = True)
        image = Image.objects.get(pk = 1)
        self.assertRedirects(
            response,
            reverse('image_edit_basic', kwargs = {'id': 1}),
            status_code = 302,
            target_status_code = 200)
        self.assertEqual(image.watermark, True)
        self.assertEqual(image.watermark_text, "Watermark test")
        self.assertEqual(image.watermark_position, 0)
        self.assertEqual(image.watermark_opacity, 100)

        # Test basic settings
        response = self.client.post(
            reverse('image_edit_save_basic'),
            {
                'image_id': 1,
                'submit_gear': True,
                'title': "Test title",
                'link': "http://www.example.com",
                'link_to_fits': "http://www.example.com/fits",
                'subject_type': 600,
                'solar_system_main_subject': 0,
                'locations': [],
                'description': "Image description",
                'allow_comments': True
            },
            follow = True)
        image = Image.objects.get(pk = 1)
        self.assertRedirects(
            response,
            reverse('image_edit_gear', kwargs = {'id': 1}),
            status_code = 302,
            target_status_code = 200)
        self.assertEqual(image.title, "Test title")
        self.assertEqual(image.link, "http://www.example.com")
        self.assertEqual(image.link_to_fits, "http://www.example.com/fits")
        self.assertEqual(image.subject_type, 600)
        self.assertEqual(image.solar_system_main_subject, 0)
        self.assertEqual(image.locations.count(), 0)
        self.assertEqual(image.description, "Image description")
        self.assertEqual(image.allow_comments, True)
