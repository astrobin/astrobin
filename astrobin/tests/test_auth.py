from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase

class LoginTest(TestCase):
    def test_login_view(self):
        User.objects.create_user('test', 'test@test.com', 'password')

        response = self.client.post(
            '/account/login/',
            {
                'auth-username': 'test',
                'auth-password': 'password',
                'login_view-current_step': 'auth',
            })

        self.assertRedirects(response, '/')

    def test_email_login_view(self):
        User.objects.create_user('test', 'test@test.com', 'password')

        response = self.client.post(
            '/account/login/',
            {
                'auth-username': 'test@test.com',
                'auth-password': 'password',
                'login_view-current_step': 'auth',
            })

        self.assertRedirects(response, '/')

    def test_case_sensitive_login_view(self):
        User.objects.create_user('test', 'test@test.com', 'password')
        User.objects.create_user('Test', 'test2@test.com', 'password2')

        response = self.client.post(
            '/account/login/',
            {
                'auth-username': 'test',
                'auth-password': 'password',
                'login_view-current_step': 'auth',
            })

        self.assertRedirects(response, '/')

        self.client.logout()

        response = self.client.post(
            '/account/login/',
            {
                'auth-username': 'Test',
                'auth-password': 'password2',
                'login_view-current_step': 'auth',
            })

        self.assertRedirects(response, '/')

    def test_case_insensitive_login_view(self):
        User.objects.create_user('test', 'test@test.com', 'password')

        response = self.client.post(
            '/account/login/',
            {
                'auth-username': 'Test',
                'auth-password': 'password',
                'login_view-current_step': 'auth',
            })

        self.assertRedirects(response, '/')

    def test_password_reset_view(self):
        response = self.client.get(reverse('password_reset'))
        self.assertEqual(response.status_code, 200)
