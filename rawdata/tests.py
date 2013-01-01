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

# Other AstroBin apps
from astrobin.models import Image

# This app
from .forms import (
    PrivateSharedFolderForm,
)
from .models import (
    PrivateSharedFolder,
    RawImage,
    TemporaryArchive,
)
from .utils import md5_for_file


# Utility functions
def max_id(Klass):
    new_id = Klass.objects.aggregate(Max('id'))['id__max']
    if new_id is None:
        new_id = 1
    return new_id


def setup_data(testcase):
    testcase.unsubscribed_user = User.objects.create_user('username_unsub', 'fake0@email.tld', 'passw0rd')
    testcase.subscribed_user = User.objects.create_user('username_sub', 'fake1@email.tld', 'passw0rd')
    testcase.subscribed_user_2 = User.objects.create_user('username_sub_2', 'fake2@email.tld', 'passw0rd')
    testcase.group = Group.objects.create(name = 'rawdata-meteor')
    testcase.group.user_set.add(testcase.subscribed_user, testcase.subscribed_user_2)
    testcase.subscription = Subscription.objects.create(
        name = 'test_subscription',
        price = 1.0,
        group = testcase.group)
    testcase.user_subscription = UserSubscription.objects.create(
        user = testcase.subscribed_user,
        subscription = testcase.subscription,
        cancelled = False)
    testcase.user_subscription_2 = UserSubscription.objects.create(
        user = testcase.subscribed_user_2,
        subscription = testcase.subscription,
        cancelled = False)


def teardown_data(testcase):
    testcase.subscribed_user.delete()
    testcase.unsubscribed_user.delete()
    testcase.group.delete()
    testcase.subscription.delete()
    testcase.user_subscription.delete()


def get_file():
    f = open('rawdata/fixtures/test.fit', 'rb')
    h = md5_for_file(f)

    f.seek(0)
    return f, h


def test_response(testcase, url, data, expected_status_code = 200,
                  expected_field = None, expected_message = None):
    response = testcase.client.post(url, data)
    response_json = json.loads(response.content)
    testcase.assertEquals(response.status_code, expected_status_code)
    if expected_field:
        testcase.assertEquals(
            response_json[expected_field][0],
            expected_message)

    return response_json

def upload_file(testcase):
    f, h = get_file()
    testcase.client.login(username = 'username_sub', password = 'passw0rd')
    response = test_response(
        testcase,
        reverse('api.rawdata.rawimage.list'),
        {'file': f, 'file_hash': h},
        201)
    testcase.client.logout()
    return response['id']


class RawImageTest(TestCase):
    def setUp(self):
        setup_data(self)
       
    def tearDown(self):
        teardown_data(self)


     #########################################################################
    ###########################################################################
    ### C R E A T I O N                                                     ###
     #########################################################################

    def test_api_create_anon(self):
        f, h = get_file()
        test_response(self, reverse('api.rawdata.rawimage.list'), {'file': f}, 403)
        f.close()

    def test_api_create_unsub(self):
        f, h = get_file()
        self.client.login(username = 'username_unsub', password = 'passw0rd')
        test_response(self, reverse('api.rawdata.rawimage.list'), {'file': f}, 403)
        self.client.logout()
        f.close()

    def test_api_create_sub_missing_file(self):
        f, h = get_file()
        self.client.login(username = 'username_sub', password = 'passw0rd')
        test_response(self, reverse('api.rawdata.rawimage.list'), {}, 400,
                            'file', "This field is required.")
        self.client.logout()
        f.close()

    def test_api_create_sub_invalid_hash(self):
        f, h = get_file()
        self.client.login(username = 'username_sub', password = 'passw0rd')
        test_response(self, reverse('api.rawdata.rawimage.list'),
                            {'file': f, 'file_hash': 'abcd'}, 400, 'non_field_errors',
                            "file_hash abcd doesn't match uploaded file, whose hash is %s" % h)
        self.client.logout()
        f.close()

    def test_api_create_sub_success(self):
        f, h = get_file()
        self.client.login(username = 'username_sub', password = 'passw0rd')
        test_response(self, reverse('api.rawdata.rawimage.list'), {'file': f}, 201)
        self.client.logout()
        f.close()

     #########################################################################
    ###########################################################################
    ### D O W N L O A D                                                     ###
     #########################################################################

    def test_download_anon(self):
        rawimage_id = upload_file(self)
        response = self.client.get(reverse('rawdata.download', kwargs = {'ids': rawimage_id}))
        self.assertRedirects(
            response,
            'http://testserver/accounts/login/?next=/rawdata/download/%d/' % rawimage_id,
            status_code = 302, target_status_code = 200)

    def test_download_unsub(self):
        rawimage_id = upload_file(self)
        self.client.login(username = 'username_unsub', password = 'passw0rd')
        response = self.client.get(reverse('rawdata.download', kwargs = {'ids': rawimage_id}), follow = True)
        self.assertRedirects(
            response,
            reverse('rawdata.restricted') + '?' + urlencode({'next': '/rawdata/download/%d/' % rawimage_id}),
            status_code = 302, target_status_code = 200)
        self.client.logout()

    def test_download_sub(self):
        rawimage_id = upload_file(self)
        self.client.login(username = 'username_sub', password = 'passw0rd')
        response = self.client.get(reverse('rawdata.download', kwargs = {'ids': rawimage_id}))
        newid = max_id(TemporaryArchive)
        self.assertRedirects(
            response,
            reverse('rawdata.temporary_archive_detail', args = (newid,)),
            status_code = 302, target_status_code = 200)
        self.client.logout()

    def test_download_multi_sub(self):
        rawimage1_id = upload_file(self)
        rawimage2_id = upload_file(self)

        self.client.login(username = 'username_sub', password = 'passw0rd')
        response = self.client.get(reverse('rawdata.download',
            kwargs = {'ids': '%d,%d' % (rawimage1_id, rawimage2_id)}))
        newid = max_id(TemporaryArchive)
        self.assertRedirects(
            response,
            reverse('rawdata.temporary_archive_detail', args = (newid,)),
            status_code = 302, target_status_code = 200)
        self.client.logout()

     #########################################################################
    ###########################################################################
    ### D E L E T E                                                         ###
     #########################################################################

    def test_delete_anon(self):
        rawimage_id = upload_file(self)
        response = self.client.delete(reverse('rawdata.delete', kwargs = {'ids': rawimage_id}))
        self.assertRedirects(
            response,
            'http://testserver/accounts/login/?next=/rawdata/delete/%d/' % rawimage_id,
            status_code = 302, target_status_code = 200)

    def test_delete_unsub(self):
        rawimage_id = upload_file(self)
        self.client.login(username = 'username_unsub', password = 'passw0rd')
        response = self.client.delete(reverse('rawdata.delete', kwargs = {'ids': rawimage_id}), follow = True)
        self.assertRedirects(
            response,
            reverse('rawdata.restricted') + '?' + urlencode({'next': '/rawdata/delete/%d/' % rawimage_id}),
            status_code = 302, target_status_code = 200)
        self.client.logout()

    def test_delete_sub(self):
        rawimage_id = upload_file(self)
        self.client.login(username = 'username_sub', password = 'passw0rd')
        response = self.client.delete(
            reverse('rawdata.delete', kwargs = {'ids': rawimage_id}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RawImage.objects.filter(id = rawimage_id).count(), 0)
        self.client.logout()

    def test_delete_multi_sub(self):
        rawimage_id_1 = upload_file(self)
        rawimage_id_2 = upload_file(self)

        self.client.login(username = 'username_sub', password = 'passw0rd')
        response = self.client.delete(
            reverse('rawdata.delete', kwargs = {'ids': "%d,%d" % (rawimage_id_1, rawimage_id_2)}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RawImage.objects.filter(id = rawimage_id_1).count(), 0)
        self.assertEqual(RawImage.objects.filter(id = rawimage_id_2).count(), 0)
        self.client.logout()

    def test_delete_wrong_sub(self):
        rawimage_id = upload_file(self)
        self.client.login(username = 'username_sub_2', password = 'passw0rd')
        response = self.client.delete(
            reverse('rawdata.delete', kwargs = {'ids': rawimage_id}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(RawImage.objects.filter(id = rawimage_id).count(), 1)
        self.client.logout()


class PrivateSharedFolderTest(TestCase):
    def setUp(self):
        setup_data(self)
       
    def tearDown(self):
        teardown_data(self)

     #########################################################################
    ###########################################################################
    ### L I S T                                                             ###
     #########################################################################

    def test_list_anon(self):
        response = self.client.get(reverse('rawdata.privatesharedfolder_list'), follow = True)
        self.assertRedirects(
            response,
            'http://testserver/accounts/login/?next=/rawdata/privatesharedfolders/',
            status_code = 302, target_status_code = 200)

    def test_list_unsub(self):
        self.client.login(username = 'username_unsub', password = 'passw0rd')
        response = self.client.get(reverse('rawdata.privatesharedfolder_list'), follow = True)
        self.assertRedirects(
            response,
            reverse('rawdata.restricted') + '?' + urlencode({'next': '/rawdata/privatesharedfolders/'}),
            status_code = 302, target_status_code = 200)
        self.client.logout()

    def test_list_sub(self):
        self.client.login(username = 'username_sub', password = 'passw0rd')
        response = self.client.get(reverse('rawdata.privatesharedfolder_list'))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

     #########################################################################
    ###########################################################################
    ### D E T A I L                                                         ###
     #########################################################################

    def test_detail_anon(self):
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        response = self.client.get(
            reverse('rawdata.privatesharedfolder_detail', args = (folder.id,)),
            follow = True)
        self.assertRedirects(
            response,
            'http://testserver/accounts/login/?next=/rawdata/privatesharedfolders/%d/' % folder.id,
            status_code = 302, target_status_code = 200)

    def test_detail_unsub(self):
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        self.client.login(username = 'username_unsub', password = 'passw0rd')
        response = self.client.get(
            reverse('rawdata.privatesharedfolder_detail', args = (folder.id,)),
            follow = True)

        self.assertRedirects(
            response,
            reverse('rawdata.restricted') + '?' + urlencode({'next': '/rawdata/privatesharedfolders/%d/' % folder.id}),
            status_code = 302, target_status_code = 200)
        self.client.logout()

    def test_detail_sub(self):
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        self.client.login(username = 'username_sub', password = 'passw0rd')

        response = self.client.get(
            reverse('rawdata.privatesharedfolder_detail', args = (folder.id,)),
            follow = True)

        self.assertEqual(response.status_code, 200)
        self.client.logout()

     #########################################################################
    ###########################################################################
    ### C R E A T I O N                                                     ###
     #########################################################################

    def test_create_anon(self):
        rawimage_id = upload_file(self)
        response = self.client.get(reverse('rawdata.privatesharedfolder_create', kwargs = {'ids': rawimage_id}))
        self.assertRedirects(
            response,
            'http://testserver/accounts/login/?next=/rawdata/privatesharedfolders/share/%d/' % rawimage_id,
            status_code = 302, target_status_code = 200)

    def test_create_unsub(self):
        rawimage_id = upload_file(self)
        self.client.login(username = 'username_unsub', password = 'passw0rd')
        response = self.client.get(reverse('rawdata.privatesharedfolder_create', kwargs = {'ids': rawimage_id}), follow = True)
        self.assertRedirects(
            response,
            reverse('rawdata.restricted') + '?' + urlencode({'next': '/rawdata/privatesharedfolders/share/%d/' % rawimage_id}),
            status_code = 302, target_status_code = 200)
        self.client.logout()

    def test_create_sub(self):
        rawimage_id = upload_file(self)
        self.client.login(username = 'username_sub', password = 'passw0rd')
        response = self.client.get(reverse('rawdata.privatesharedfolder_create', kwargs = {'ids': rawimage_id}))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

     #########################################################################
    ###########################################################################
    ### U P D A T E                                                         ###
     #########################################################################

    def test_update_anon(self):
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        post_data = {'name': "changed name", 'description': "changed description"}
        response = self.client.post(
            reverse('rawdata.privatesharedfolder_update', args = (folder.id,)),
            post_data)
        self.assertRedirects(
            response,
            'http://testserver/accounts/login/?next=/rawdata/privatesharedfolders/%d/update/' % folder.id,
            status_code = 302, target_status_code = 200)

    def test_update_unsub(self):
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        self.client.login(username = 'username_unsub', password = 'passw0rd')
        post_data = {'name': "changed name", 'description': "changed description"}
        response = self.client.post(
            reverse('rawdata.privatesharedfolder_update', args = (folder.id,)),
            post_data)
        self.assertEqual(response.status_code, 404)
        self.client.logout()

    def test_update_sub(self):
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        post_data = {'name': "", 'description': "changed description"}
        self.client.login(username = 'username_sub', password = 'passw0rd')
        response = self.client.post(
            reverse('rawdata.privatesharedfolder_update', args = (folder.id,)),
            post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)

        post_data = {'name': "changed name", 'description': ""}
        response = self.client.post(
            reverse('rawdata.privatesharedfolder_update', args = (folder.id,)),
            post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)

        post_data = {'name': "changed name", 'description': "changed description"}
        response = self.client.post(
            reverse('rawdata.privatesharedfolder_update', args = (folder.id,)),
            post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.client.logout()

        folder = PrivateSharedFolder.objects.get(id = folder.id)
        self.assertEqual(folder.name, "changed name")
        self.assertEqual(folder.description, "changed description")

     #########################################################################
    ###########################################################################
    ### D E L E T E                                                         ###
     #########################################################################

    def test_delete_anon(self):
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        response = self.client.delete(
            reverse('rawdata.privatesharedfolder_delete', args = (folder.id,)))
        self.assertRedirects(
            response,
            'http://testserver/accounts/login/?next=/rawdata/privatesharedfolders/%d/delete/' % folder.id,
            status_code = 302, target_status_code = 200)

        count = PrivateSharedFolder.objects.filter(id = folder.id).count()
        self.assertEqual(count, 1)

    def test_delete_unsub(self):
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        self.client.login(username = 'username_unsub', password = 'passw0rd')
        response = self.client.delete(
            reverse('rawdata.privatesharedfolder_delete', args = (folder.id,)),
            follow = True)
        self.assertRedirects(
            response,
            reverse('rawdata.restricted') + '?' + urlencode({'next': '/rawdata/privatesharedfolders/%d/delete/' % folder.id}),
            status_code = 302, target_status_code = 200)

        self.client.logout()

        count = PrivateSharedFolder.objects.filter(id = folder.id).count()
        self.assertEqual(count, 1)

    def test_delete_sub(self):
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        self.client.login(username = 'username_sub', password = 'passw0rd')
        response = self.client.delete(
            reverse('rawdata.privatesharedfolder_delete', args = (folder.id,)),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        self.client.logout()

        count = PrivateSharedFolder.objects.filter(id = folder.id).count()
        self.assertEqual(count, 0)

     #########################################################################
    ###########################################################################
    ### A D D   D A T A                                                     ###
     #########################################################################

    def test_add_data_anon(self):
        rawimage_id = upload_file(self)
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        post_data = {'images': rawimage_id}
        response = self.client.post( reverse('rawdata.privatesharedfolder_add_data', args = (folder.id,)),
            post_data,
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest')
        self.assertRedirects(
            response,
            'http://testserver/accounts/login/?next=/rawdata/privatesharedfolders/%d/add-data/' % folder.id,
            status_code = 302, target_status_code = 200)

    def test_add_data_unsub(self):
        rawimage_id = upload_file(self)
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        post_data = {'images': rawimage_id}
        self.client.login(username = 'username_unsub', password = 'passw0rd')
        response = self.client.post(
            reverse('rawdata.privatesharedfolder_add_data', args = (folder.id,)),
            post_data,
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest',
            follow = True)
        self.assertRedirects(
            response,
            reverse('rawdata.restricted') + '?' + urlencode({'next': '/rawdata/privatesharedfolders/%d/add-data/' % folder.id}),
            status_code = 302, target_status_code = 200)
        self.client.logout()

    def test_add_data_sub(self):
        rawimage_id = upload_file(self)

        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        post_data = {'images': rawimage_id}
        self.client.login(username = 'username_sub', password = 'passw0rd')
        response = self.client.post(
            reverse('rawdata.privatesharedfolder_add_data', args = (folder.id,)),
            post_data,
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest')
        self.client.logout()

        folder = PrivateSharedFolder.objects.get(id = folder.id)
        self.assertEqual(folder.images.all().count(), 1)

    def test_add_data_multi_sub(self):
        rawimage_id_1 = upload_file(self)
        rawimage_id_2 = upload_file(self)

        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        post_data = {'images': (rawimage_id_1, rawimage_id_2)}
        self.client.login(username = 'username_sub', password = 'passw0rd')
        response = self.client.post(
            reverse('rawdata.privatesharedfolder_add_data', args = (folder.id,)),
            post_data,
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest')
        self.client.logout()

        folder = PrivateSharedFolder.objects.get(id = folder.id)
        self.assertEqual(folder.images.all().count(), 2)

    def test_add_data_wrong_sub(self):
        rawimage_id = upload_file(self)
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        post_data = {'images': rawimage_id}
        self.client.login(username = 'username_sub_2', password = 'passw0rd')
        response = self.client.post(
            reverse('rawdata.privatesharedfolder_add_data', args = (folder.id,)),
            post_data,
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest')
        self.assertEqual(response.status_code, 404)
        self.client.logout()

        folder = PrivateSharedFolder.objects.get(id = folder.id)
        self.assertEqual(folder.images.all().count(), 0)

    def test_add_data_sub_invitee(self):
        rawimage_id = upload_file(self)
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        folder.users.add(self.subscribed_user_2)

        post_data = {'images': rawimage_id}
        self.client.login(username = 'username_sub_2', password = 'passw0rd')
        response = self.client.post(
            reverse('rawdata.privatesharedfolder_add_data', args = (folder.id,)),
            post_data,
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest')
        self.client.logout()

        folder = PrivateSharedFolder.objects.get(id = folder.id)
        self.assertEqual(folder.images.all().count(), 1)

     #########################################################################
    ###########################################################################
    ### R E M O V E   D A T A                                               ###
     #########################################################################

    def test_remove_data_anon(self):
        rawimage_id = upload_file(self)
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        folder.images.add(rawimage_id)

        response = self.client.post(
            reverse('rawdata.privatesharedfolder_remove_data',
                    kwargs = {'pk': folder.id, 'rawimage_pk': rawimage_id}),
            {},
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest')
        self.assertRedirects(
            response,
            'http://testserver/accounts/login/?next=/rawdata/privatesharedfolders/%d/remove-data/%d/' % (folder.id, rawimage_id),
            status_code = 302, target_status_code = 200)

    def test_remove_data_unsub(self):
        rawimage_id = upload_file(self)
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        folder.images.add(rawimage_id)

        self.client.login(username = 'username_unsub', password = 'passw0rd')
        response = self.client.post(
            reverse('rawdata.privatesharedfolder_remove_data',
                    kwargs = {'pk': folder.id, 'rawimage_pk': rawimage_id}),
            {},
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest',
            follow = True)
        self.assertRedirects(
            response,
            reverse('rawdata.restricted') + '?' + urlencode({'next': '/rawdata/privatesharedfolders/%d/remove-data/%d/' % (folder.id, rawimage_id)}),
            status_code = 302, target_status_code = 200)
        self.client.logout()

    def test_remove_data_sub(self):
        rawimage_id = upload_file(self)

        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        folder.images.add(rawimage_id)

        self.assertEqual(folder.images.all().count(), 1)

        self.client.login(username = 'username_sub', password = 'passw0rd')
        response = self.client.post(
            reverse('rawdata.privatesharedfolder_remove_data',
                    kwargs = {'pk': folder.id, 'rawimage_pk': rawimage_id}),
            {},
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest')
        self.client.logout()

        folder = PrivateSharedFolder.objects.get(id = folder.id)
        self.assertEqual(folder.images.all().count(), 0)

    def test_remove_data_wrong_sub(self):
        rawimage_id = upload_file(self)
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        folder.images.add(rawimage_id)

        self.client.login(username = 'username_sub_2', password = 'passw0rd')
        response = self.client.post(
            reverse('rawdata.privatesharedfolder_remove_data',
                    kwargs = {'pk': folder.id, 'rawimage_pk': rawimage_id}),
            {},
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest')
        self.assertEqual(response.status_code, 404)
        self.client.logout()

        folder = PrivateSharedFolder.objects.get(id = folder.id)
        self.assertEqual(folder.images.all().count(), 1)

    def test_remove_data_sub_invitee(self):
        rawimage_id = upload_file(self)
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        folder.users.add(self.subscribed_user_2)
        folder.images.add(rawimage_id)

        self.client.login(username = 'username_sub_2', password = 'passw0rd')
        response = self.client.post(
            reverse('rawdata.privatesharedfolder_remove_data',
                    kwargs = {'pk': folder.id, 'rawimage_pk': rawimage_id}),
            {},
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest')
        self.assertEqual(response.status_code, 404)
        self.client.logout()

        folder = PrivateSharedFolder.objects.get(id = folder.id)
        self.assertEqual(folder.images.all().count(), 1)

     #########################################################################
    ###########################################################################
    ### A D D   I M A G E                                                   ###
     #########################################################################

    def test_add_image_anon(self):
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        image = Image.objects.create(title = "test image", user = self.subscribed_user)

        post_data = {'image': image.id}
        response = self.client.post( reverse('rawdata.privatesharedfolder_add_image', args = (folder.id,)),
            post_data,
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest')
        self.assertRedirects(
            response,
            'http://testserver/accounts/login/?next=/rawdata/privatesharedfolders/%d/add-image/' % folder.id,
            status_code = 302, target_status_code = 200)

    def test_add_image_unsub(self):
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        image = Image.objects.create(title = "test image", user = self.subscribed_user)

        post_data = {'image': image.id}
        self.client.login(username = 'username_unsub', password = 'passw0rd')
        response = self.client.post(
            reverse('rawdata.privatesharedfolder_add_image', args = (folder.id,)),
            post_data,
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest',
            follow = True)
        self.assertRedirects(
            response,
            reverse('rawdata.restricted') + '?' + urlencode({'next': '/rawdata/privatesharedfolders/%d/add-image/' % folder.id}),
            status_code = 302, target_status_code = 200)
        self.client.logout()

    def test_add_image_sub(self):
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        image = Image.objects.create(title = "test image", user = self.subscribed_user)

        post_data = {'image': image.id}
        self.client.login(username = 'username_sub', password = 'passw0rd')
        response = self.client.post(
            reverse('rawdata.privatesharedfolder_add_image', args = (folder.id,)),
            post_data,
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest')
        self.client.logout()

        folder = PrivateSharedFolder.objects.get(id = folder.id)
        self.assertEqual(folder.processed_images.all().count(), 1)

    def test_add_image_wrong_sub(self):
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        image = Image.objects.create(title = "test image", user = self.subscribed_user_2)

        post_data = {'image': image.id}
        self.client.login(username = 'username_sub_2', password = 'passw0rd')
        response = self.client.post(
            reverse('rawdata.privatesharedfolder_add_image', args = (folder.id,)),
            post_data,
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest')
        self.assertEqual(response.status_code, 404)
        self.client.logout()

        folder = PrivateSharedFolder.objects.get(id = folder.id)
        self.assertEqual(folder.processed_images.all().count(), 0)

    def test_add_image_sub_invitee(self):
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        folder.users.add(self.subscribed_user_2)
        image = Image.objects.create(title = "test image", user = self.subscribed_user_2)

        post_data = {'image': image.id}
        self.client.login(username = 'username_sub_2', password = 'passw0rd')
        response = self.client.post(
            reverse('rawdata.privatesharedfolder_add_image', args = (folder.id,)),
            post_data,
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest')
        self.client.logout()

        folder = PrivateSharedFolder.objects.get(id = folder.id)
        self.assertEqual(folder.processed_images.all().count(), 1)

     #########################################################################
    ###########################################################################
    ### A D D   U S E R                                                     ###
     #########################################################################

    def test_add_users_anon(self):
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        post_data = {'users': self.subscribed_user_2}
        response = self.client.post(reverse('rawdata.privatesharedfolder_add_users', args = (folder.id,)),
            post_data,
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest')
        self.assertRedirects(
            response,
            'http://testserver/accounts/login/?next=/rawdata/privatesharedfolders/%d/add-users/' % folder.id,
            status_code = 302, target_status_code = 200)

    def test_add_users_unsub(self):
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        post_data = {'users': self.subscribed_user_2}
        self.client.login(username = 'username_unsub', password = 'passw0rd')
        response = self.client.post(
            reverse('rawdata.privatesharedfolder_add_users', args = (folder.id,)),
            post_data,
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest',
            follow = True)
        self.assertRedirects(
            response,
            reverse('rawdata.restricted') + '?' + urlencode({'next': '/rawdata/privatesharedfolders/%d/add-users/' % folder.id}),
            status_code = 302, target_status_code = 200)
        self.client.logout()

    def test_add_users_sub(self):
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        post_data = {'users': self.subscribed_user_2}
        self.client.login(username = 'username_sub', password = 'passw0rd')
        response = self.client.post(
            reverse('rawdata.privatesharedfolder_add_users', args = (folder.id,)),
            post_data,
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest')
        self.client.logout()

        folder = PrivateSharedFolder.objects.get(id = folder.id)
        self.assertEqual(folder.users.all().count(), 1)

    def test_add_users_multi_sub(self):
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        post_data = {'users': "%s,%s" % (self.subscribed_user_2, self.unsubscribed_user)}
        self.client.login(username = 'username_sub', password = 'passw0rd')
        response = self.client.post(
            reverse('rawdata.privatesharedfolder_add_users', args = (folder.id,)),
            post_data,
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest')
        self.client.logout()

        folder = PrivateSharedFolder.objects.get(id = folder.id)
        self.assertEqual(folder.users.all().count(), 2)

    def test_add_users_wrong_sub(self):
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        post_data = {'users': self.subscribed_user_2}
        self.client.login(username = 'username_sub_2', password = 'passw0rd')
        response = self.client.post(
            reverse('rawdata.privatesharedfolder_add_users', args = (folder.id,)),
            post_data,
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest')
        self.assertEqual(response.status_code, 404)
        self.client.logout()

        folder = PrivateSharedFolder.objects.get(id = folder.id)
        self.assertEqual(folder.users.all().count(), 0)

    def test_add_users_sub_invitee(self):
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        folder.users.add(self.subscribed_user_2)

        post_data = {'users': self.subscribed_user_2}
        self.client.login(username = 'username_sub_2', password = 'passw0rd')
        response = self.client.post(
            reverse('rawdata.privatesharedfolder_add_users', args = (folder.id,)),
            post_data,
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest')
        self.client.logout()

        folder = PrivateSharedFolder.objects.get(id = folder.id)
        self.assertEqual(folder.users.all().count(), 1)

     #########################################################################
    ###########################################################################
    ### R E M O V E   U S E R                                               ###
     #########################################################################

    def test_remove_user_anon(self):
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        folder.users.add(self.subscribed_user_2)

        response = self.client.post(
            reverse('rawdata.privatesharedfolder_remove_user',
                    kwargs = {'pk': folder.id, 'user_id': self.subscribed_user_2.id}),
            {},
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest')
        self.assertRedirects(
            response,
            'http://testserver/accounts/login/?next=/rawdata/privatesharedfolders/%d/remove-user/%d/' % (folder.id, self.subscribed_user_2.id),
            status_code = 302, target_status_code = 200)

    def test_remove_user_unsub(self):
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        folder.users.add(self.subscribed_user_2)

        self.client.login(username = 'username_unsub', password = 'passw0rd')
        response = self.client.post(
            reverse('rawdata.privatesharedfolder_remove_user',
                    kwargs = {'pk': folder.id, 'user_id': self.subscribed_user_2.id}),
            {},
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest',
            follow = True)
        self.assertRedirects(
            response,
            reverse('rawdata.restricted') + '?' + urlencode({'next': '/rawdata/privatesharedfolders/%d/remove-user/%d/' % (folder.id, self.subscribed_user_2.id)}),
            status_code = 302, target_status_code = 200)
        self.client.logout()

    def test_remove_user_sub(self):
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        folder.users.add(self.subscribed_user_2)

        self.assertEqual(folder.users.all().count(), 1)

        self.client.login(username = 'username_sub', password = 'passw0rd')
        response = self.client.post(
            reverse('rawdata.privatesharedfolder_remove_user',
                    kwargs = {'pk': folder.id, 'user_id': self.subscribed_user_2.id}),
            {},
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest')
        self.client.logout()

        folder = PrivateSharedFolder.objects.get(id = folder.id)
        self.assertEqual(folder.users.all().count(), 0)

    def test_remove_user_wrong_sub(self):
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        folder.users.add(self.unsubscribed_user)

        self.client.login(username = 'username_sub_2', password = 'passw0rd')
        response = self.client.post(
            reverse('rawdata.privatesharedfolder_remove_user',
                    kwargs = {'pk': folder.id, 'user_id': self.unsubscribed_user.id}),
            {},
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest')
        self.assertEqual(response.status_code, 404)
        self.client.logout()

        folder = PrivateSharedFolder.objects.get(id = folder.id)
        self.assertEqual(folder.users.all().count(), 1)

    def test_remove_user_sub_invitee(self):
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        folder.users.add(self.subscribed_user_2)
        folder.users.add(self.unsubscribed_user)

        self.client.login(username = 'username_sub_2', password = 'passw0rd')
        response = self.client.post(
            reverse('rawdata.privatesharedfolder_remove_user',
                    kwargs = {'pk': folder.id, 'user_id': self.unsubscribed_user.id}),
            {},
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest')
        self.assertEqual(response.status_code, 404)
        self.client.logout()

        folder = PrivateSharedFolder.objects.get(id = folder.id)
        self.assertEqual(folder.users.all().count(), 2)

     #########################################################################
    ###########################################################################
    ### D O W N L O A D                                                     ###
     #########################################################################

    def test_download_anon(self):
        rawimage_id = upload_file(self)

        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        folder.images.add(rawimage_id)

        response = self.client.get(reverse('rawdata.privatesharedfolder_download', args = (folder.id,)))
        self.assertRedirects(
            response,
            'http://testserver/accounts/login/?next=/rawdata/privatesharedfolders/%d/download/' % folder.id,
            status_code = 302, target_status_code = 200)

    def test_download_unsub(self):
        rawimage_id = upload_file(self)

        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        folder.images.add(rawimage_id)

        self.client.login(username = 'username_unsub', password = 'passw0rd')
        response = self.client.get(reverse('rawdata.privatesharedfolder_download', args = (folder.id,)), follow = True)
        self.assertRedirects(
            response,
            reverse('rawdata.restricted') + '?' + urlencode({'next': '/rawdata/privatesharedfolders/%d/download/' % folder.id}),
            status_code = 302, target_status_code = 200)
        self.client.logout()

    def test_download_sub(self):
        rawimage_id = upload_file(self)

        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        folder.images.add(rawimage_id)

        self.client.login(username = 'username_sub', password = 'passw0rd')
        response = self.client.get(reverse('rawdata.privatesharedfolder_download', args = (folder.id,)), follow = True)
        newid = max_id(TemporaryArchive)
        self.assertRedirects(
            response,
            reverse('rawdata.temporary_archive_detail', args = (newid,)),
            status_code = 302, target_status_code = 200)
        self.client.logout()

    def test_download_wrong_sub(self):
        rawimage_id = upload_file(self)

        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        folder.images.add(rawimage_id)

        self.client.login(username = 'username_sub_2', password = 'passw0rd')
        response = self.client.get(reverse('rawdata.privatesharedfolder_download', args = (folder.id,)), follow = True)
        self.assertEqual(response.status_code, 404)
