import datetime

from django.contrib.auth.models import Group, User
from django.core.urlresolvers import reverse
from django.test import TestCase
from mock import patch
from mock import patch

from astrobin.models import Image


class ModerationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('user', 'user@test.com', 'password')
        self.moderator = User.objects.create_user('moderator', 'moderator@test.com', 'password')
        self.superuser = User.objects.create_superuser('superuser', 'superuser@test.com', 'password')

        self.content_moderators = Group.objects.create(name='content_moderators')
        self.image_moderators = Group.objects.create(name='image_moderators')

        self.moderator.groups.add(self.content_moderators, self.image_moderators)

    def tearDown(self):
        self.content_moderators.delete()
        self.image_moderators.delete()
        self.user.delete()
        self.moderator.delete()
        self.superuser.delete()

    def _do_upload(self, filename, wip=False):
        data = {'image_file': open(filename, 'rb')}
        if wip:
            data['wip'] = True

        patch('astrobin.tasks.retrieve_primary_thumbnails.delay')
        return self.client.post(
            reverse('image_upload_process'),
            data,
            follow=True)

    def _get_last_image(self):
        return Image.objects_including_wip.all().order_by('-id')[0]

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_image_moderation_queue_view(self, retrieve_primary_thumbnails):
        # Anon cannot access
        response = self.client.get(reverse('image_moderation'))
        self.assertEqual(response.status_code, 403)

        # Non moderator cannot access
        self.client.login(username='user', password='password')
        response = self.client.get(reverse('image_moderation'))
        self.assertEqual(response.status_code, 403)

        # Moderator can access
        self.client.login(username='moderator', password='password')
        response = self.client.get(reverse('image_moderation'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The moderation queue is empty")

        # Upload an image that requires moderation
        self.client.login(username='user', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        image.title = "Moderation test"
        image.save(keep_deleted=True)

        self.client.login(username='moderator', password='password')

        # An image that was just uploaded is not there
        response = self.client.get(reverse('image_moderation'))
        self.assertNotContains(response, "Moderation test")

        # We need to make it be 10 minutes in the past
        image.uploaded = datetime.datetime.now() - datetime.timedelta(minutes=11)
        image.save(keep_deleted=True)

        # Moderator can see the image in the queue
        response = self.client.get(reverse('image_moderation'))
        self.assertContains(response, "Moderation test")

        # Moderator can approve it
        response = self.client.post(reverse('image_moderation_mark_as_ham'), {'ids[]': [image.pk]})
        self.assertEqual(response.status_code, 200)
        image = Image.objects_including_wip.get(pk=image.pk)
        self.assertEqual(image.moderator_decision, 1)

        # Moderator can mark it as spam
        image.moderator_decision = 0
        image.save(keep_deleted=True)
        response = self.client.post(reverse('image_moderation_mark_as_spam'), {'ids[]': [image.pk]})
        self.assertEqual(response.status_code, 200)
        image = Image.objects_including_wip.get(pk=image.pk)
        self.assertEqual(image.moderator_decision, 2)

        image.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_spam_user_gallery(self, retrieve_primary_thumbnails):
        self.client.login(username='user', password='password')
        response = self.client.get(reverse('user_page', args=('user',)))
        self.assertEquals(response.status_code, 200)

        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        image.moderator_decision = 2
        image.save(keep_deleted=True)

        # Same user gets 404
        response = self.client.get(reverse('user_page', args=('user',)))
        self.assertEquals(response.status_code, 404)

        # Anon gets 404
        self.client.logout()
        response = self.client.get(reverse('user_page', args=('user',)))
        self.assertEquals(response.status_code, 404)

        # Moderator gets 200
        self.client.login(username='moderator', password='password')
        response = self.client.get(reverse('user_page', args=('user',)))
        self.assertEquals(response.status_code, 200)

        # Superuser gets 200
        self.client.login(username='superuser', password='password')
        response = self.client.get(reverse('user_page', args=('user',)))
        self.assertEquals(response.status_code, 200)
