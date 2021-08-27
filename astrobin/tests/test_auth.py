from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase

class LoginTest(TestCase):
    def test_login_view(self):
        User.objects.create_user('test', 'test@test.com', 'password')

        response = self.client.post(
            '/accounts/login/',
            {
                'username': 'test',
                'password': 'password',
            })

        self.assertRedirects(response, '/')

    def test_email_login_view(self):
        User.objects.create_user('test', 'test@test.com', 'password')

        response = self.client.post(
            '/accounts/login/',
            {
                'username': 'test@test.com',
                'password': 'password',
            })

        self.assertRedirects(response, '/')

    def test_case_sensitive_login_view(self):
        User.objects.create_user('test', 'test@test.com', 'password')
        User.objects.create_user('Test', 'test2@test.com', 'password2')

        response = self.client.post(
            '/accounts/login/',
            {
                'username': 'test',
                'password': 'password',
            })

        self.assertRedirects(response, '/')

        self.client.logout()

        response = self.client.post(
            '/accounts/login/',
            {
                'username': 'Test',
                'password': 'password2',
            })

        self.assertRedirects(response, '/')

    def test_case_insensitive_login_view(self):
        User.objects.create_user('test', 'test@test.com', 'password')

        response = self.client.post(
            '/accounts/login/',
            {
                'username': 'Test',
                'password': 'password',
            })

        self.assertRedirects(response, '/')

    def test_password_reset_view(self):
        response = self.client.get(reverse('password_reset'))
        self.assertEqual(response.status_code, 200)
