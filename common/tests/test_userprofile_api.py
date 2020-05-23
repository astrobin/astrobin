import simplejson as json

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse_lazy
from django.test import TestCase


class CommonTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'user', 'user@test.com', 'password')

    def tearDown(self):
        self.user.delete()

    def test_real_name_in_user_api(self):
        """
        Tests the userprofile.real_name field is available in the user api.
        """
        self.user.userprofile.real_name = 'Real Name'
        self.user.userprofile.save(keep_deleted=True)

        self.client.login(username='user', password='password')

        response = json.loads(self.client.get(
            reverse_lazy('user-detail', args=(self.user.pk,))).content)
        self.assertTrue('userprofile' in response)
        self.assertEqual(self.user.userprofile.pk, response['userprofile'])

        response = json.loads(self.client.get(
            reverse_lazy('userprofile-detail', args=(self.user.userprofile.pk,))).content)
        self.assertTrue('real_name' in response)
        self.assertEqual('Real Name', response['real_name'])
