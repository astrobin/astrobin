from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase
from threaded_messages.models import Thread

from astrobin.tests.generators import Generators
from astrobin_apps_premium.services.premium_service import SubscriptionName


class MessagesTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('user', 'user@test.com', 'password')
        self.user2 = User.objects.create_user('user2', 'user2@test.com', 'password')

    def test_messages_page_opens(self):
        self.client.login(username='user', password='password')

        response = self.client.get(reverse('messages_inbox'))

        self.assertEqual(response.status_code, 200)

    def test_messages_page_when_logged_out(self):
        response = self.client.get(reverse('messages_inbox'), follow=True)

        self.assertRedirects(
            response,
            '/account/login/?next=/messages/inbox/',
            status_code=302, target_status_code=200)

    def test_messages_send(self):
        subject = 'I am a subject'
        self.client.login(username='user', password='password')

        response = self.client.post(reverse('messages_compose'), {
            'recipient': 'user2',
            'subject': subject,
            'body': 'I am a body',
            'g-recaptcha-response': '1',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, subject)

        self.client.logout()
        self.client.login(username='user2', password='password')

        response = self.client.get(reverse('messages_inbox'))

        self.assertContains(response, subject)

    def test_messages_view(self):
        subject = 'I am a subject'
        body = 'I am a body'

        self.client.login(username='user', password='password')

        self.client.post(reverse('messages_compose'), {
            'recipient': 'user2',
            'subject': subject,
            'body': body,
            'g-recaptcha-response': '1',
        }, follow=True)

        thread = Thread.objects.all()[0]  # type: Thread

        response = self.client.get(reverse('messages_detail', args=(thread.id,)), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, subject)
        self.assertContains(response, body)

    def test_messages_view_paid_account(self):
        subject = 'I am a subject'
        body = 'I am a body'

        Generators.premium_subscription(self.user, SubscriptionName.ULTIMATE_2020)

        self.client.login(username='user', password='password')

        self.client.post(reverse('messages_compose'), {
            'recipient': 'user2',
            'subject': subject,
            'body': body,
            # No 'g-recaptcha-response' parameter!
        }, follow=True)

        thread: Thread = Thread.objects.all()[0]

        response = self.client.get(reverse('messages_detail', args=(thread.id,)), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, subject)
        self.assertContains(response, body)
