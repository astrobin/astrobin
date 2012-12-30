# Python
import json

# Django
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.db.models import Max
from django.test import TestCase
from django.utils.http import urlencode

# Third party apps
from subscription.models import Subscription, UserSubscription

# This app
from .models import RawImage, TemporaryArchive
from .utils import md5_for_file


# Utility functions
def max_id(Klass):
    new_id = Klass.objects.aggregate(Max('id'))['id__max']
    if new_id is None:
        new_id = 1
    return new_id


class RawImageTest(TestCase):
    def setUp(self):
        self.unsubscribed_user = User.objects.create_user('username_unsub', 'fake0@email.tld', 'passw0rd')
        self.subscribed_user = User.objects.create_user('username_sub', 'fake1@email.tld', 'passw0rd')
        self.subscribed_user_2 = User.objects.create_user('username_sub_2', 'fake2@email.tld', 'passw0rd')
        self.group = Group.objects.create(name = 'rawdata-meteor')
        self.group.user_set.add(self.subscribed_user, self.subscribed_user_2)
        self.subscription = Subscription.objects.create(
            name = 'test_subscription',
            price = 1.0,
            group = self.group)
        self.user_subscription = UserSubscription.objects.create(
            user = self.subscribed_user,
            subscription = self.subscription,
            cancelled = False)
        self.user_subscription_2 = UserSubscription.objects.create(
            user = self.subscribed_user_2,
            subscription = self.subscription,
            cancelled = False)
        
    def tearDown(self):
        self.subscribed_user.delete()
        self.unsubscribed_user.delete()
        self.group.delete()
        self.subscription.delete()
        self.user_subscription.delete()

    def _test_response(self, url, data, expected_status_code = 200,
                       expected_field = None, expected_message = None):
        response = self.client.post(url, data)
        response_json = json.loads(response.content)
        self.assertEquals(response.status_code, expected_status_code)
        if expected_field:
            self.assertEquals(
                response_json[expected_field][0],
                expected_message)

        return response_json

    def _get_file(self):
        f = open('rawdata/fixtures/test.fit', 'rb')
        h = md5_for_file(f)

        f.seek(0)
        return f, h

    def _upload_file(self):
        f, h = self._get_file()
        self.client.login(username = 'username_sub', password = 'passw0rd')
        response = self._test_response(
            reverse('api.rawdata.rawimage.list'),
            {'file': f, 'file_hash': h},
            201)
        self.client.logout()
        return response['id']

     ######################################################################### 
    ###########################################################################
    ### C R E A T I O N                                                     ###
     #########################################################################

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

     ######################################################################### 
    ###########################################################################
    ### D O W N L O A D                                                     ###
     #########################################################################

    def test_download_anon(self):
        rawimage_id = self._upload_file()
        response = self.client.get(reverse('rawdata.download', kwargs = {'ids': rawimage_id}))
        self.assertRedirects(
            response,
            'http://testserver/accounts/login/?next=/rawdata/download/%d/' % rawimage_id,
            status_code = 302, target_status_code = 200)

    def test_download_unsub(self):
        rawimage_id = self._upload_file()
        self.client.login(username = 'username_unsub', password = 'passw0rd')
        response = self.client.get(reverse('rawdata.download', kwargs = {'ids': rawimage_id}), follow = True)
        self.assertRedirects(
            response,
            reverse('rawdata.restricted') + '?' + urlencode({'next': '/rawdata/download/%d/' % rawimage_id}),
            status_code = 302, target_status_code = 200)

    def test_download_sub(self):
        rawimage_id = self._upload_file()
        self.client.login(username = 'username_sub', password = 'passw0rd')
        response = self.client.get(reverse('rawdata.download', kwargs = {'ids': rawimage_id}))
        newid = max_id(TemporaryArchive)
        self.assertRedirects(
            response,
            reverse('rawdata.temporary_archive_detail', args = (newid,)),
            status_code = 302, target_status_code = 200)

    def test_download_multi_sub(self):
        rawimage1_id = self._upload_file()
        rawimage2_id = self._upload_file()

        self.client.login(username = 'username_sub', password = 'passw0rd')
        response = self.client.get(reverse('rawdata.download',
            kwargs = {'ids': '%d,%d' % (rawimage1_id, rawimage2_id)}))
        newid = max_id(TemporaryArchive)
        self.assertRedirects(
            response,
            reverse('rawdata.temporary_archive_detail', args = (newid,)),
            status_code = 302, target_status_code = 200)

     ######################################################################### 
    ###########################################################################
    ### D E L E T E                                                         ###
     #########################################################################

    def test_delete_anon(self):
        rawimage_id = self._upload_file()
        response = self.client.delete(reverse('rawdata.delete', kwargs = {'ids': rawimage_id}))
        self.assertRedirects(
            response,
            'http://testserver/accounts/login/?next=/rawdata/delete/%d/' % rawimage_id,
            status_code = 302, target_status_code = 200)

    def test_delete_unsub(self):
        rawimage_id = self._upload_file()
        self.client.login(username = 'username_unsub', password = 'passw0rd')
        response = self.client.delete(reverse('rawdata.delete', kwargs = {'ids': rawimage_id}), follow = True)
        self.assertRedirects(
            response,
            reverse('rawdata.restricted') + '?' + urlencode({'next': '/rawdata/delete/%d/' % rawimage_id}),
            status_code = 302, target_status_code = 200)

    def test_delete_sub(self):
        rawimage_id = self._upload_file()
        self.client.login(username = 'username_sub', password = 'passw0rd')
        response = self.client.delete(
            reverse('rawdata.delete', kwargs = {'ids': rawimage_id}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RawImage.objects.filter(id = rawimage_id).count(), 0)

    def test_delete_multi_sub(self):
        rawimage_id_1 = self._upload_file()
        rawimage_id_2 = self._upload_file()

        self.client.login(username = 'username_sub', password = 'passw0rd')
        response = self.client.delete(
            reverse('rawdata.delete', kwargs = {'ids': "%d,%d" % (rawimage_id_1, rawimage_id_2)}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RawImage.objects.filter(id = rawimage_id_1).count(), 0)
        self.assertEqual(RawImage.objects.filter(id = rawimage_id_2).count(), 0)

    def test_delete_wrong_sub(self):
        rawimage_id = self._upload_file()
        self.client.login(username = 'username_sub_2', password = 'passw0rd')
        response = self.client.delete(
            reverse('rawdata.delete', kwargs = {'ids': rawimage_id}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(RawImage.objects.filter(id = rawimage_id).count(), 1)

