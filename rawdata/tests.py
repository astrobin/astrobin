# Python
import json

# Django
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.test import TestCase

# Third party apps
from subscription.models import Subscription, UserSubscription

# This app
from .models import RawImage
from .utils import md5_for_file

class RawImageTest(TestCase):
    def get_file(self):
        f = open('rawdata/fixtures/test.fit', 'rb')
        return f, md5_for_file(f)

    def setUp(self):
        self.user = User.objects.create_user('username', 'fake@email.tld', 'passw0rd')
        self.group = Group.objects.create(name = 'rawdata-meteor')
        self.group.user_set.add(self.user)
        self.subscription = Subscription.objects.create(
            name = 'test_subscription',
            price = 1.0,
            group = self.group)
        self.user_subscription = UserSubscription.objects.create(
            user = self.user,
            subscription = self.subscription,
            cancelled = False)

    def test_api_create(self):
        def test_response(data, expected_status_code,
                          expected_field = None, expected_message = None):
            response = self.client.post(reverse('api.rawdata.rawimage.list'), data)
            self.assertEquals(response.status_code, expected_status_code)
            if expected_field:
                self.assertEquals(
                    json.loads(response.content)[expected_field][0],
                    expected_message)

        f, h = self.get_file()
        self.client.login(username = 'username', password = 'passw0rd')

        # Test missing file
        f.seek(0)
        test_response({}, 400, 'file', "This field is required.")

        # Test for success
        f.seek(0)
        test_response({'file': f}, 201)

        # Test for invalid hash
        f.seek(0)
        test_response({'file': f, 'file_hash': 'abcd'}, 400, 'non_field_errors',
                      "file_hash abcd doesn't match uploaded file, whose hash is %s" % h)

        f.close()

    def tearDown(self):
        self.user.delete()
