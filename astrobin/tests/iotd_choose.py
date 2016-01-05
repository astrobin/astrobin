# Python
import datetime

# Django
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.test import TestCase

# AstroBin
from astrobin.models import Image, ImageOfTheDay


class IOTDChooseTest(TestCase):
    def _assert_message(self, response, tags, content):
        storage = response.context[0]['messages']
        for message in storage:
            self.assertEqual(message.tags, tags)
            self.assertTrue(content in message.message)

    def test_page_exists(self):
        response = self.client.get(reverse('iotd_choose'))
        self.assertEqual(response.status_code, 302)

    def test_page_accessible_by_iotd_staff(self):
        user = User.objects.create_user('test', 'test@test.com', 'password')
        self.client.login(username = 'test', password = 'password')
        response = self.client.get(reverse('iotd_choose'))
        self.assertEqual(response.status_code, 403)


        group = Group.objects.create(name = 'IOTD_Staff')
        user.groups.add(group)
        response = self.client.get(reverse('iotd_choose'))
        self.assertEqual(response.status_code, 200)

        group.delete()
        user.delete()

    def test_iotd_already_exists(self):
        user = User.objects.create_user('test', 'test@test.com', 'password')
        group = Group.objects.create(name = 'IOTD_Staff')
        user.groups.add(group)
        self.client.login(username = 'test', password = 'password')

        image, created = Image.objects.get_or_create(user = user)
        iotd, created = ImageOfTheDay.objects.get_or_create(
            image = image, date = datetime.date.today)

        response = self.client.get(reverse('iotd_choose'))
        self._assert_message(response, "error unread", "was already chosen")

        iotd.delete()
        image.delete()
        group.delete()
        user.delete()
