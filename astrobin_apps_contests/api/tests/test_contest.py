from datetime import datetime, date, timedelta

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from astrobin_apps_contests.models import Contest


class ContestTests(APITestCase):
    valid_data = {
        'title': 'Test contest',
        'description': 'Test description',
        'rules': 'Test rules',
        'prizes': 'Test prizes',
        'start_date': "2100-01-01",
        'end_date': "2100-01-08",
        'min_participants': 10,
        'max_participants': 100,
    }

    def test_create_contest_as_anonymous(self):
        """
        Anonymous users should not be able to create contests.
        """
        response = self.client.post(reverse('contest-list'), self.valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_contest_as_non_admin(self):
        """
        Non-admin users should not be able to create contests.
        """
        User.objects.create_user(username="test", password="test")
        self.client.login(username="test", password="test")
        response = self.client.post(reverse('contest-list'), self.valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_create_contest(self):
        """
        Admin users should not be able to create contests.
        """
        user = User.objects.create_superuser(username="test", email="test@test.com", password="test")
        self.client.login(username="test", password="test")

        url = reverse('contest-list')

        response = self.client.post(url, self.valid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Contest.objects.count(), 1)
        self.assertEqual(Contest.objects.get().title, self.valid_data['title'])
        self.assertEqual(Contest.objects.get().description, self.valid_data['description'])
        self.assertEqual(Contest.objects.get().rules, self.valid_data['rules'])
        self.assertEqual(Contest.objects.get().prizes, self.valid_data['prizes'])
        self.assertEqual(Contest.objects.get().start_date, date(2100, 1, 1))
        self.assertEqual(Contest.objects.get().end_date, date(2100, 1, 8))
        self.assertEqual(Contest.objects.get().min_participants, self.valid_data['min_participants'])
        self.assertEqual(Contest.objects.get().max_participants, self.valid_data['max_participants'])
        self.assertEqual(Contest.objects.get().user, user)

    def test_create_contest_title_is_required(self):
        """
        The title field should be required.
        """
        User.objects.create_superuser(username="test", email="test@test.com", password="test")
        self.client.login(username="test", password="test")

        url = reverse('contest-list')
        data = self.valid_data
        data['title'] = None

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_contest_description_is_required(self):
        """
        The description field should be required.
        """
        User.objects.create_superuser(username="test", email="test@test.com", password="test")
        self.client.login(username="test", password="test")

        url = reverse('contest-list')
        data = self.valid_data
        data['description'] = None

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_contest_start_date_too_early(self):
        """
        The start date should be at least a week from now.
        """
        User.objects.create_superuser(username="test", email="test@test.com", password="test")
        self.client.login(username="test", password="test")

        url = reverse('contest-list')
        data = self.valid_data
        data['start_date'] = date.today() + timedelta(days=6)

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_contest_end_date_too_early(self):
        """
        The start date should be at least two weeks from now.
        """
        User.objects.create_superuser(username="test", email="test@test.com", password="test")
        self.client.login(username="test", password="test")

        url = reverse('contest-list')
        data = self.valid_data
        data['end_date'] = date.today() + timedelta(days=13)

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_contest_end_date_before_start_date(self):
        """
        The start date and end date should be separated by a week or more
        """
        User.objects.create_superuser(username="test", email="test@test.com", password="test")
        self.client.login(username="test", password="test")

        url = reverse('contest-list')
        data = self.valid_data
        data['end_date'] = "2099-12-31"

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_contest_duration_not_enough(self):
        """
        The start date and end date should be separated by a week or more
        """
        User.objects.create_superuser(username="test", email="test@test.com", password="test")
        self.client.login(username="test", password="test")

        url = reverse('contest-list')
        data = self.valid_data
        data['end_date'] = "2100-01-07"

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_contest_as_anonymous(self):
        """
        Anonymous users should be able to list contests.
        """
        response = self.client.get(reverse('contest-list'), self.valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
