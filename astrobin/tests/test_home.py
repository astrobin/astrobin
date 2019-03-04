# Python
from mock import patch

# Django
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

# Test stuff
from astrobin.tests.common import *


class HomeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test', 'test@test.com', 'password')

    def tearDown(self):
        self.user.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_global_stream(self, retrieve_primary_thumbnails):
        url = reverse('index') + '?s=global'
        self.client.login(username = 'test', password = 'password')

        # Uploading an image shows up in the stream
        response, image = test_utils_upload_image(self)
        test_utils_approve_image(image)
        response = self.client.get(url)
        self.assertContains(response, 'VERB_UPLOADED_IMAGE.%d.%d' % (self.user.pk, image.pk))

        # Uploading another image shows up in the stream too
        response, image2 = test_utils_upload_image(self)
        test_utils_approve_image(image2)
        response = self.client.get(url)
        self.assertContains(response, 'VERB_UPLOADED_IMAGE.%d.%d' % (self.user.pk, image2.pk))

        # Uploading a revision removes the action about the image upload
        response, revision = test_utils_upload_revision(self, image)
        response = self.client.get(url)
        self.assertNotContains(response, 'VERB_UPLOADED_IMAGE.%d.%d' % (self.user.pk, image.pk))
        # Still contains action for image2 tho
        self.assertContains(response, 'VERB_UPLOADED_IMAGE.%d.%d' % (self.user.pk, image2.pk))
        self.assertContains(response, 'VERB_UPLOADED_REVISION.%d.%d' % (self.user.pk, revision.pk))

        # Uploading another revision removes the previous revisions' stream actions
        response, revision2 = test_utils_upload_revision(self, image)
        response = self.client.get(url)
        self.assertNotContains(response, 'VERB_UPLOADED_REVISION.%d.%d' % (self.user.pk, revision.pk))
        self.assertContains(response, 'VERB_UPLOADED_REVISION.%d.%d' % (self.user.pk, revision2.pk))
