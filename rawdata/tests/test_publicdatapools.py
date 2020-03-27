# Django
from django.core.urlresolvers import reverse
from django.test import TransactionTestCase
from django.utils.http import urlencode

# Other AstroBin apps
from astrobin.models import Image

# This app
from astrobin.tests.generators import Generators
from rawdata.models import PublicDataPool, TemporaryArchive

# Tests
from .test_common import *


class PublicDataPoolTest(TransactionTestCase):
    def setUp(self):
        setup_data(self)

    def tearDown(self):
        teardown_data(self)

     #########################################################################
    ###########################################################################
    ### L I S T                                                             ###
     #########################################################################

    def test_list_anon(self):
        response = self.client.get(reverse('rawdata.publicdatapool_list'), follow = True)
        self.assertEqual(response.status_code, 200)

    def test_list_unsub(self):
        self.client.login(username = 'username_unsub', password = 'passw0rd')
        response = self.client.get(reverse('rawdata.publicdatapool_list'), follow = True)
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_list_sub(self):
        self.client.login(username = 'username_sub', password = 'passw0rd')
        response = self.client.get(reverse('rawdata.publicdatapool_list'))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

     #########################################################################
    ###########################################################################
    ### D E T A I L                                                         ###
     #########################################################################

    def test_detail_anon(self):
        pool = PublicDataPool(
            name = "test pool",
            description = "test description",
            creator = self.subscribed_user)
        pool.save()

        response = self.client.get(
            reverse('rawdata.publicdatapool_detail', args = (pool.id,)),
            follow = True)
        self.assertEqual(response.status_code, 200)

    def test_detail_unsub(self):
        pool = PublicDataPool(
            name = "test pool",
            description = "test description",
            creator = self.subscribed_user)
        pool.save()

        self.client.login(username = 'username_unsub', password = 'passw0rd')
        response = self.client.get(
            reverse('rawdata.publicdatapool_detail', args = (pool.id,)),
            follow = True)

        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_detail_sub(self):
        pool = PublicDataPool(
            name = "test pool",
            description = "test description",
            creator = self.subscribed_user)
        pool.save()

        self.client.login(username = 'username_sub', password = 'passw0rd')

        response = self.client.get(
            reverse('rawdata.publicdatapool_detail', args = (pool.id,)),
            follow = True)

        self.assertEqual(response.status_code, 200)
        self.client.logout()

     #########################################################################
    ###########################################################################
    ### C R E A T I O N                                                     ###
     #########################################################################

    def test_create_anon(self):
        rawimage_id = upload_file(self)
        response = self.client.get(reverse('rawdata.publicdatapool_create', kwargs = {'ids': rawimage_id}))
        self.assertRedirects(
            response,
            'http://testserver/accounts/login/?next=/rawdata/publicdatapools/share/%d/' % rawimage_id,
            status_code = 302, target_status_code = 200)

    def test_create_unsub(self):
        rawimage_id = upload_file(self)
        self.client.login(username = 'username_unsub', password = 'passw0rd')
        response = self.client.get(reverse('rawdata.publicdatapool_create', kwargs = {'ids': rawimage_id}), follow = True)
        self.assertRedirects(
            response,
            reverse('rawdata.restricted') + '?' + urlencode({'next': '/rawdata/publicdatapools/share/%d/' % rawimage_id}),
            status_code = 302, target_status_code = 200)
        self.client.logout()

    def test_create_sub(self):
        rawimage_id = upload_file(self)
        self.client.login(username = 'username_sub', password = 'passw0rd')
        response = self.client.get(reverse('rawdata.publicdatapool_create', kwargs = {'ids': rawimage_id}))
        self.assertEqual(response.status_code, 200)
        self.client.logout()

     #########################################################################
    ###########################################################################
    ### U P D A T E                                                         ###
     #########################################################################

    def test_update_anon(self):
        pool = PublicDataPool(
            name = "test pool",
            description = "test description",
            creator = self.subscribed_user)
        pool.save()

        post_data = {'name': "changed name", 'description': "changed description"}
        response = self.client.post(
            reverse('rawdata.publicdatapool_update', args = (pool.id,)),
            post_data)
        self.assertRedirects(
            response,
            'http://testserver/accounts/login/?next=/rawdata/publicdatapools/%d/update/' % pool.id,
            status_code = 302, target_status_code = 200)

    def test_update_unsub(self):
        pool = PublicDataPool(
            name = "test pool",
            description = "test description",
            creator = self.subscribed_user)
        pool.save()

        self.client.login(username = 'username_unsub', password = 'passw0rd')
        post_data = {'name': "changed name", 'description': "changed description"}
        response = self.client.post(
            reverse('rawdata.publicdatapool_update', args = (pool.id,)),
            post_data)
        self.assertEqual(response.status_code, 404)
        self.client.logout()

    def test_update_sub(self):
        pool = PublicDataPool(
            name = "test pool",
            description = "test description",
            creator = self.subscribed_user)
        pool.save()

        post_data = {'name': "", 'description': "changed description"}
        self.client.login(username = 'username_sub', password = 'passw0rd')
        response = self.client.post(
            reverse('rawdata.publicdatapool_update', args = (pool.id,)),
            post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)

        post_data = {'name': "changed name", 'description': ""}
        response = self.client.post(
            reverse('rawdata.publicdatapool_update', args = (pool.id,)),
            post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)

        post_data = {'name': "changed name", 'description': "changed description"}
        response = self.client.post(
            reverse('rawdata.publicdatapool_update', args = (pool.id,)),
            post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.client.logout()

        pool = PublicDataPool.objects.get(id = pool.id)
        self.assertEqual(pool.name, "changed name")
        self.assertEqual(pool.description, "changed description")

     #########################################################################
    ###########################################################################
    ### A D D   D A T A                                                     ###
     #########################################################################

    def test_add_data_anon(self):
        rawimage_id = upload_file(self)
        pool = PublicDataPool(
            name = "test pool",
            description = "test description",
            creator = self.subscribed_user)
        pool.save()

        post_data = {'images': rawimage_id}
        response = self.client.post( reverse('rawdata.publicdatapool_add_data', args = (pool.id,)),
            post_data,
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest')
        self.assertRedirects(
            response,
            'http://testserver/accounts/login/?next=/rawdata/publicdatapools/%d/add-data/' % pool.id,
            status_code = 302, target_status_code = 200)

    def test_add_data_unsub(self):
        rawimage_id = upload_file(self)
        pool = PublicDataPool(
            name = "test pool",
            description = "test description",
            creator = self.subscribed_user)
        pool.save()

        post_data = {'images': rawimage_id}
        self.client.login(username = 'username_unsub', password = 'passw0rd')
        response = self.client.post(
            reverse('rawdata.publicdatapool_add_data', args = (pool.id,)),
            post_data,
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest',
            follow = True)
        self.assertRedirects(
            response,
            reverse('rawdata.restricted') + '?' + urlencode({'next': '/rawdata/publicdatapools/%d/add-data/' % pool.id}),
            status_code = 302, target_status_code = 200)
        self.client.logout()

    def test_add_data_sub(self):
        rawimage_id = upload_file(self)

        pool = PublicDataPool(
            name = "test pool",
            description = "test description",
            creator = self.subscribed_user)
        pool.save()

        post_data = {'images': rawimage_id}
        self.client.login(username = 'username_sub', password = 'passw0rd')
        response = self.client.post(
            reverse('rawdata.publicdatapool_add_data', args = (pool.id,)),
            post_data,
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest')
        self.client.logout()

        pool = PublicDataPool.objects.get(id = pool.id)
        self.assertEqual(pool.images.all().count(), 1)

    def test_add_data_multi_sub(self):
        rawimage_id_1 = upload_file(self)
        rawimage_id_2 = upload_file(self)

        pool = PublicDataPool(
            name = "test pool",
            description = "test description",
            creator = self.subscribed_user)
        pool.save()

        post_data = {'images': (rawimage_id_1, rawimage_id_2)}
        self.client.login(username = 'username_sub', password = 'passw0rd')
        response = self.client.post(
            reverse('rawdata.publicdatapool_add_data', args = (pool.id,)),
            post_data,
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest')
        self.client.logout()

        pool = PublicDataPool.objects.get(id = pool.id)
        self.assertEqual(pool.images.all().count(), 2)

     #########################################################################
    ###########################################################################
    ### R E M O V E   D A T A                                               ###
     #########################################################################

    def test_remove_data_anon(self):
        rawimage_id = upload_file(self)
        pool = PublicDataPool(
            name = "test pool",
            description = "test description",
            creator = self.subscribed_user)
        pool.save()

        pool.images.add(rawimage_id)

        response = self.client.post(
            reverse('rawdata.publicdatapool_remove_data',
                    kwargs = {'pk': pool.id, 'rawimage_pk': rawimage_id}),
            {},
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest')
        self.assertRedirects(
            response,
            'http://testserver/accounts/login/?next=/rawdata/publicdatapools/%d/remove-data/%d/' % (pool.id, rawimage_id),
            status_code = 302, target_status_code = 200)

    def test_remove_data_unsub(self):
        rawimage_id = upload_file(self)
        pool = PublicDataPool(
            name = "test pool",
            description = "test description",
            creator = self.subscribed_user)
        pool.save()

        pool.images.add(rawimage_id)

        self.client.login(username = 'username_unsub', password = 'passw0rd')
        response = self.client.post(
            reverse('rawdata.publicdatapool_remove_data',
                    kwargs = {'pk': pool.id, 'rawimage_pk': rawimage_id}),
            {},
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest',
            follow = True)
        self.assertRedirects(
            response,
            reverse('rawdata.restricted') + '?' + urlencode({'next': '/rawdata/publicdatapools/%d/remove-data/%d/' % (pool.id, rawimage_id)}),
            status_code = 302, target_status_code = 200)
        self.client.logout()

    def test_remove_data_sub(self):
        rawimage_id = upload_file(self)

        pool = PublicDataPool(
            name = "test pool",
            description = "test description",
            creator = self.subscribed_user)
        pool.save()

        pool.images.add(rawimage_id)

        self.assertEqual(pool.images.all().count(), 1)

        self.client.login(username = 'username_sub', password = 'passw0rd')
        response = self.client.post(
            reverse('rawdata.publicdatapool_remove_data',
                    kwargs = {'pk': pool.id, 'rawimage_pk': rawimage_id}),
            {},
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest')
        self.client.logout()

        pool = PublicDataPool.objects.get(id = pool.id)
        self.assertEqual(pool.images.all().count(), 0)

     #########################################################################
    ###########################################################################
    ### A D D   I M A G E                                                   ###
     #########################################################################

    def test_add_image_anon(self):
        pool = PublicDataPool(
            name = "test pool",
            description = "test description",
            creator = self.subscribed_user)
        pool.save()

        image = Image.objects.create(title = "test image", user = self.subscribed_user)

        post_data = {'image': image.id}
        response = self.client.post( reverse('rawdata.publicdatapool_add_image', args = (pool.id,)),
            post_data,
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest')
        self.assertRedirects(
            response,
            'http://testserver/accounts/login/?next=/rawdata/publicdatapools/%d/add-image/' % pool.id,
            status_code = 302, target_status_code = 200)

    def test_add_image_unsub(self):
        pool = PublicDataPool(
            name = "test pool",
            description = "test description",
            creator = self.subscribed_user)
        pool.save()

        image = Image.objects.create(title = "test image", user = self.subscribed_user)

        post_data = {'image': image.id}
        self.client.login(username = 'username_unsub', password = 'passw0rd')
        response = self.client.post(
            reverse('rawdata.publicdatapool_add_image', args = (pool.id,)),
            post_data,
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.client.logout()

        pool = PublicDataPool.objects.get(id = pool.id)
        self.assertEqual(pool.processed_images.all().count(), 1)

    def test_add_image_sub(self):
        pool = PublicDataPool(
            name = "test pool",
            description = "test description",
            creator = self.subscribed_user)
        pool.save()

        image = Image.objects.create(title = "test image", user = self.subscribed_user)

        post_data = {'image': image.id}
        self.client.login(username = 'username_sub', password = 'passw0rd')
        response = self.client.post(
            reverse('rawdata.publicdatapool_add_image', args = (pool.id,)),
            post_data,
            HTTP_X_REQUESTED_WITH = 'XMLHttpRequest')
        self.client.logout()

        pool = PublicDataPool.objects.get(id = pool.id)
        self.assertEqual(pool.processed_images.all().count(), 1)

     #########################################################################
    ###########################################################################
    ### D O W N L O A D                                                     ###
     #########################################################################

    def test_download_anon(self):
        rawimage_id = upload_file(self)

        pool = PublicDataPool(
            name = "test pool",
            description = "test description",
            creator = self.subscribed_user)
        pool.save()

        pool.images.add(rawimage_id)

        response = self.client.get(reverse('rawdata.publicdatapool_download', args = (pool.id,)))
        self.assertRedirects(
            response,
            'http://testserver/accounts/login/?next=/rawdata/publicdatapools/%d/download/' % pool.id,
            status_code = 302, target_status_code = 200)

    def test_download_unsub(self):
        rawimage_id = upload_file(self)

        pool = PublicDataPool(
            name = "test pool",
            description = "test description",
            creator = self.subscribed_user)
        pool.save()

        pool.images.add(rawimage_id)

        self.client.login(username = 'username_unsub', password = 'passw0rd')
        response = self.client.get(reverse('rawdata.publicdatapool_download', args = (pool.id,)), follow = True)
        self.assertEquals(response.status_code, 403)

        self.client.logout()

    def test_download_sub_but_not_premium(self):
        rawimage_id = upload_file(self)

        pool = PublicDataPool(
            name = "test pool",
            description = "test description",
            creator = self.subscribed_user)
        pool.save()

        pool.images.add(rawimage_id)

        self.client.login(username = 'username_sub', password = 'passw0rd')
        response = self.client.get(reverse('rawdata.publicdatapool_download', args = (pool.id,)), follow = True)
        self.assertEquals(response.status_code, 403)

        self.client.logout()

    def test_download_sub_and_premium(self):
        rawimage_id = upload_file(self)

        pool = PublicDataPool(
            name="test pool",
            description="test description",
            creator=self.subscribed_user)
        pool.save()

        pool.images.add(rawimage_id)

        us = Generators.premium_subscription(self.subscribed_user, "AstroBin Ultimate 2020+")

        self.client.login(username='username_sub', password='passw0rd')
        response = self.client.get(reverse('rawdata.publicdatapool_download', args=(pool.id,)), follow=True)
        newid = max_id(TemporaryArchive)
        self.assertRedirects(
            response,
            reverse('rawdata.temporary_archive_detail', args=(newid,)),
            status_code=302, target_status_code=200)

        self.client.logout()
        us.delete()
