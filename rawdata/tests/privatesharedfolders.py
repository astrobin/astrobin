# Django
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.http import urlencode

# Other AstroBin apps
from astrobin.models import Image

# This app
from rawdata.models import PrivateSharedFolder, TemporaryArchive

# Tests
from .common import *


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
        response = self.client.get(reverse('rawdata.privatesharedfolder_list'))
        self.assertEqual(response.status_code, 200)
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

    def test_detail_unsub_uninvited(self):
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        self.client.login(username = 'username_unsub', password = 'passw0rd')
        response = self.client.get(
            reverse('rawdata.privatesharedfolder_detail', args = (folder.id,)))
        self.assertEqual(response.status_code, 404)
        self.client.logout()

    def test_detail_unsub_invited(self):
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        folder.users.add(self.unsubscribed_user)

        self.client.login(username = 'username_unsub', password = 'passw0rd')
        response = self.client.get(
            reverse('rawdata.privatesharedfolder_detail', args = (folder.id,)))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_detail_sub_uninvited(self):
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        self.client.login(username = 'username_sub_2', password = 'passw0rd')
        response = self.client.get(
            reverse('rawdata.privatesharedfolder_detail', args = (folder.id,)))
        self.assertEqual(response.status_code, 404)
        self.client.logout()

    def test_detail_sub_invited(self):
        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        folder.users.add(self.subscribed_user_2)

        self.client.login(username = 'username_sub_2', password = 'passw0rd')

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

    def test_download_unsub_uninvited(self):
        rawimage_id = upload_file(self)

        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        folder.images.add(rawimage_id)

        self.client.login(username = 'username_unsub', password = 'passw0rd')
        response = self.client.get(reverse('rawdata.privatesharedfolder_download', args = (folder.id,)))
        self.assertEqual(response.status_code, 404)
        self.client.logout()

    def test_download_unsub_invited(self):
        rawimage_id = upload_file(self)

        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        folder.users.add(self.unsubscribed_user)
        folder.images.add(rawimage_id)

        self.client.login(username = 'username_unsub', password = 'passw0rd')
        response = self.client.get(reverse('rawdata.privatesharedfolder_download', args = (folder.id,)), follow = True)
        newid = max_id(TemporaryArchive)
        self.assertRedirects(
            response,
            reverse('rawdata.temporary_archive_detail', args = (newid,)),
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

    def test_download_invitee(self):
        rawimage_id = upload_file(self)

        folder = PrivateSharedFolder(
            name = "test folder",
            description = "test description",
            creator = self.subscribed_user)
        folder.save()

        folder.images.add(rawimage_id)
        folder.users.add(self.subscribed_user_2)

        self.client.login(username = 'username_sub_2', password = 'passw0rd')
        response = self.client.get(reverse('rawdata.privatesharedfolder_download', args = (folder.id,)), follow = True)
        newid = max_id(TemporaryArchive)
        self.assertRedirects(
            response,
            reverse('rawdata.temporary_archive_detail', args = (newid,)),
            status_code = 302, target_status_code = 200)
        self.client.logout()
