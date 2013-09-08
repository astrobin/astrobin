# Django
from django.contrib.auth.models import User
from django.test import TestCase

class LoginTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'test', 'test@test.com', 'password')

    def tearDown(self):
        self.user.delete()

    def test_login(self):
        response = self.client.post(
            '/accounts/login/',
            {
                'username': 'test',
                'password': 'password',
            })

        self.assertRedirects(response, '/')
