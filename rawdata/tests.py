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
    def setUp(self):
        self.unsubscribed_user = User.objects.create_user('username_unsub', 'fake0@email.tld', 'passw0rd')
        self.subscribed_user = User.objects.create_user('username_sub', 'fake1@email.tld', 'passw0rd')
        self.group = Group.objects.create(name = 'rawdata-meteor')
        self.group.user_set.add(self.subscribed_user)
        self.subscription = Subscription.objects.create(
            name = 'test_subscription',
            price = 1.0,
            group = self.group)
        self.user_subscription = UserSubscription.objects.create(
            user = self.subscribed_user,
            subscription = self.subscription,
            cancelled = False)

    def _test_response(self, url, data, expected_status_code = 200,
                       expected_field = None, expected_message = None):
        response = self.client.post(url, data)
        self.assertEquals(response.status_code, expected_status_code)
        if expected_field:
            self.assertEquals(
                json.loads(response.content)[expected_field][0],
                expected_message)

    def _get_file(self):
        f = open('rawdata/fixtures/test.fit', 'rb')
        h = md5_for_file(f)

        f.seek(0)
        return f, h

    def test_api_create_anon(self):
        f, h = self._get_file()
        self._test_response(reverse('api.rawdata.rawimage.list'), {'file': f}, 403)
        f.close()

    def test_api_create_unsub(self):
        f, h = self._get_file()
        self.client.login(username = 'username_unsub', password = 'passw0rd')
        self._test_response(reverse('api.rawdata.rawimage.list'), {'file': f}, 403)
        f.close()

    def test_api_create_sub_missing_file(self):
        f, h = self._get_file()
        self.client.login(username = 'username_sub', password = 'passw0rd')
        self._test_response(reverse('api.rawdata.rawimage.list'), {}, 400,
                            'file', "This field is required.")
        f.close()

    def test_api_create_sub_invalid_hash(self):
        f, h = self._get_file()
        self.client.login(username = 'username_sub', password = 'passw0rd')
        self._test_response(reverse('api.rawdata.rawimage.list'),
                            {'file': f, 'file_hash': 'abcd'}, 400, 'non_field_errors',
                            "file_hash abcd doesn't match uploaded file, whose hash is %s" % h)
        f.close()

    def test_api_create_sub_success(self):
        f, h = self._get_file()
        self.client.login(username = 'username_sub', password = 'passw0rd')
        self._test_response(reverse('api.rawdata.rawimage.list'), {'file': f}, 201)
        f.close()

    def tearDown(self):
        self.subscribed_user.delete()
        self.unsubscribed_user.delete()
        self.group.delete()
        self.subscription.delete()
        self.user_subscription.delete()
