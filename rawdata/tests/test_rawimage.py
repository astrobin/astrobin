# Python
import os

# Django
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.http import urlencode

# This app
from rawdata.models import RawImage, TemporaryArchive

# Tests
from .common import *


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

    def test_api_create_sub_unsupported_file(self):
        f, h = get_unsupported_file()
        self.client.login(username = 'username_sub', password = 'passw0rd')
        test_response(self, reverse('api.rawdata.rawimage.list'),
                            {'file': f, 'file_hash': h}, 415)
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

    def test_api_create_sub_quota_exceeded(self):
        f, h = get_file()
        self.client.login(username = 'username_sub_3', password = 'passw0rd')
        test_response(self, reverse('api.rawdata.rawimage.list'),
                            {'file': f}, 403)
        self.client.logout()
        f.close()


    def test_api_create_sub_success(self):
        f, h = get_file()
        self.client.login(username = 'username_sub', password = 'passw0rd')
        response = test_response(self, reverse('api.rawdata.rawimage.list'), {'file': f}, 201)
        self.assertEqual(os.path.exists(os.path.join(settings.RAWDATA_ROOT, response['file'])), True)
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

     #########################################################################
    ###########################################################################
    ### L I B R A R Y                                                       ###
     #########################################################################

    def test_library(self):
        self.client.login(username = 'username_sub', password = 'passw0rd')
        response = self.client.get(reverse('rawdata.library'))
        self.assertEqual(response.status_code, 200)
