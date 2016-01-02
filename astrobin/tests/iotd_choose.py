# Django
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.test import TestCase

class IOTDChooseTest(TestCase):
    def test_page_exists(self):
        response = self.client.get(reverse('iotd_choose'))
        self.assertEqual(response.status_code, 302)

    def test_page_accessible_by_iotd_staff(self):
        user = User.objects.create_user('test', 'test@test.com', 'password')
        group = Group.objects.create(name = 'IOTD_Staff')
        user.groups.add(group)

        self.client.login(username = 'test', password = 'password')

        response = self.client.get(reverse('iotd_choose'))
        self.assertEqual(response.status_code, 200)
