# Django
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase

class LoginTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'test', 'test@test.com', 'password')

    def tearDown(self):
        self.user.delete()

    def test_login_view(self):
        response = self.client.post(
            '/accounts/login/',
            {
                'username': 'test',
                'password': 'password',
            })

        self.assertRedirects(response, '/')

    def test_email_login_view(self):
        response = self.client.post(
            '/accounts/login/',
            {
                'username': 'test@test.com',
                'password': 'password',
            })

        self.assertRedirects(response, '/')

    def test_password_reset_view(self):
        response = self.client.get(reverse('password_reset'))
        self.assertEqual(response.status_code, 200)
