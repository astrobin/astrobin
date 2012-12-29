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
        return open('rawdata/fixtures/test.fit', 'rb')

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

    def test_hash(self):
        f = self.get_file()
        file_hash = md5_for_file(f)
        f.seek(0)
        postdata = {'file': f, 'file_hash': file_hash}

        self.client.login(username = 'username', password = 'passw0rd')

        response = self.client.post(reverse('rawimage-list'), postdata)
        self.assertEquals(response.status_code, 201)

        f.seek(0)
        postdata['file_hash'] = 'abcd' # invalid hash
        response = self.client.post(reverse('rawimage-list'), postdata)
        self.assertEquals(response.status_code, 400)

        f.close()

    def tearDown(self):
        self.user.delete()
