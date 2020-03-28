from datetime import datetime, timedelta, date

from annoying.functions import get_object_or_None
from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.urls import reverse
from subscription.models import UserSubscription, Subscription

from astrobin.tests.generators import Generators
from astrobin_apps_premium.models import DataLossCompensationRequest
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import is_ultimate_2020, is_premium


class TestDataLossCompensationRequestView(TestCase):
    def setUp(self):
        Subscription.objects.create(
            name='AstroBin Ultimate 2020+',
            price=60,
            category='premium',
            group=Group.objects.create(name='astrobin_ultimate_2020')
        )

    def test_requires_login(self):
        response = self.client.get(reverse('astrobin_apps_premium.data_loss_compensation_request'))
        self.assertRedirects(
            response,
            '/accounts/login/?next=' + reverse('astrobin_apps_premium.data_loss_compensation_request'),
            status_code=302,
            target_status_code=200)

    def test_not_eligible_does_not_have_premium(self):
        User.objects.create_user('test', 'test@test.com', 'password')
        self.client.login(username='test', password='password')
        response = self.client.get(reverse('astrobin_apps_premium.data_loss_compensation_request'))
        self.assertRedirects(
            response,
            reverse('astrobin_apps_premium.data_loss_compensation_request_not_eligible'),
            status_code=302,
            target_status_code=200)

    def test_not_eligible_premium_expired_before_incident(self):
        user = User.objects.create_user('test', 'test@test.com', 'password')
        premium = Generators.premium_subscription(user, 'AstroBin Premium')
        premium.expires = datetime(2020, 2, 14)
        premium.save()

        self.client.login(username='test', password='password')
        response = self.client.get(reverse('astrobin_apps_premium.data_loss_compensation_request'))
        self.assertRedirects(
            response,
            reverse('astrobin_apps_premium.data_loss_compensation_request_not_eligible'),
            status_code=302,
            target_status_code=200)

    def test_not_eligible_already_got_free_premium(self):
        user = User.objects.create_user('test', 'test@test.com', 'password')
        premium = Generators.premium_subscription(user, 'AstroBin Premium')
        premium.expires = datetime(2021, 2, 20)
        premium.save()

        self.client.login(username='test', password='password')
        response = self.client.get(reverse('astrobin_apps_premium.data_loss_compensation_request'))
        self.assertRedirects(
            response,
            reverse('astrobin_apps_premium.data_loss_compensation_request_not_eligible'),
            status_code=302,
            target_status_code=200)

    def test_eligible(self):
        user = User.objects.create_user('test', 'test@test.com', 'password')
        premium = Generators.premium_subscription(user, 'AstroBin Premium')
        premium.expires = datetime(2020, 2, 16)
        premium.save()

        self.client.login(username='test', password='password')
        response = self.client.get(reverse('astrobin_apps_premium.data_loss_compensation_request'))
        self.assertEquals(response.status_code, 200)

    def test_already_done(self):
        user = User.objects.create_user('test', 'test@test.com', 'password')
        premium = Generators.premium_subscription(user, 'AstroBin Premium')
        premium.expires = datetime(2020, 2, 16)
        premium.save()

        DataLossCompensationRequest.objects.create(user=user, requested_compensation='NOT_REQUIRED')

        self.client.login(username='test', password='password')
        response = self.client.get(reverse('astrobin_apps_premium.data_loss_compensation_request'))
        self.assertRedirects(
            response,
            reverse('astrobin_apps_premium.data_loss_compensation_request_already_done'),
            status_code=302,
            target_status_code=200)

    def test_submit_not_required(self):
        user = User.objects.create_user('test', 'test@test.com', 'password')
        premium = Generators.premium_subscription(user, 'AstroBin Premium')
        premium.expires = datetime(2020, 2, 16)
        premium.save()

        self.client.login(username='test', password='password')

        response = self.client.post(
            reverse('astrobin_apps_premium.data_loss_compensation_request'),
            {
                'requested_compensation': 'NOT_REQUIRED'
            })

        self.assertRedirects(
            response,
            reverse('astrobin_apps_premium.data_loss_compensation_request_success'),
            status_code=302,
            target_status_code=200)

        compensation_request = DataLossCompensationRequest.objects.get(user=user)
        self.assertEquals(compensation_request.requested_compensation, 'NOT_REQUIRED')

    def test_submit_1_mo_ultimate(self):
        user = User.objects.create_user('test', 'test@test.com', 'password')
        premium = Generators.premium_subscription(user, 'AstroBin Premium')
        premium.expires = datetime(2020, 2, 16)
        premium.save()

        self.client.login(username='test', password='password')

        response = self.client.post(
            reverse('astrobin_apps_premium.data_loss_compensation_request'),
            {
                'requested_compensation': '1_MO_ULTIMATE'
            })

        self.assertRedirects(
            response,
            reverse('astrobin_apps_premium.data_loss_compensation_request_success'),
            status_code=302,
            target_status_code=200)

        compensation_request = DataLossCompensationRequest.objects.get(user=user)
        self.assertEquals(compensation_request.requested_compensation, '1_MO_ULTIMATE')

        ultimate = get_object_or_None(UserSubscription, user=user, subscription__name='AstroBin Ultimate 2020+')
        premium = get_object_or_None(UserSubscription, user=user, subscription__name='AstroBin Premium')

        self.assertIsNotNone(ultimate)
        self.assertTrue(ultimate.active)
        self.assertTrue(ultimate.cancelled)
        self.assertTrue(ultimate.expires > date.today() + timedelta(days=29))
        self.assertTrue(ultimate.expires < date.today() + timedelta(days=31))

        self.assertTrue(is_ultimate_2020(user))

        self.assertFalse(premium.active)
        self.assertFalse(is_premium(user))

    def test_submit_3_mo_ultimate(self):
        user = User.objects.create_user('test', 'test@test.com', 'password')
        premium = Generators.premium_subscription(user, 'AstroBin Premium')
        premium.expires = datetime(2020, 2, 16)
        premium.save()

        self.client.login(username='test', password='password')

        response = self.client.post(
            reverse('astrobin_apps_premium.data_loss_compensation_request'),
            {
                'requested_compensation': '3_MO_ULTIMATE'
            })

        self.assertRedirects(
            response,
            reverse('astrobin_apps_premium.data_loss_compensation_request_success'),
            status_code=302,
            target_status_code=200)

        compensation_request = DataLossCompensationRequest.objects.get(user=user)
        self.assertEquals(compensation_request.requested_compensation, '3_MO_ULTIMATE')

        ultimate = get_object_or_None(UserSubscription, user=user, subscription__name='AstroBin Ultimate 2020+')

        self.assertIsNotNone(ultimate)
        self.assertTrue(ultimate.active)
        self.assertTrue(ultimate.cancelled)
        self.assertTrue(ultimate.expires > date.today() + timedelta(days=89))
        self.assertTrue(ultimate.expires < date.today() + timedelta(days=91))

        self.assertTrue(is_ultimate_2020(user))

    def test_submit_6_mo_ultimate(self):
        user = User.objects.create_user('test', 'test@test.com', 'password')
        premium = Generators.premium_subscription(user, 'AstroBin Premium')
        premium.expires = datetime(2020, 2, 16)
        premium.save()

        self.client.login(username='test', password='password')

        response = self.client.post(
            reverse('astrobin_apps_premium.data_loss_compensation_request'),
            {
                'requested_compensation': '6_MO_ULTIMATE'
            })

        self.assertRedirects(
            response,
            reverse('astrobin_apps_premium.data_loss_compensation_request_success'),
            status_code=302,
            target_status_code=200)

        compensation_request = DataLossCompensationRequest.objects.get(user=user)
        self.assertEquals(compensation_request.requested_compensation, '6_MO_ULTIMATE')

        ultimate = get_object_or_None(UserSubscription, user=user, subscription__name='AstroBin Ultimate 2020+')

        self.assertIsNotNone(ultimate)
        self.assertTrue(ultimate.active)
        self.assertTrue(ultimate.cancelled)
        self.assertTrue(ultimate.expires > date.today() + timedelta(days=179))
        self.assertTrue(ultimate.expires < date.today() + timedelta(days=181))

        self.assertTrue(is_ultimate_2020(user))

    def test_submit_6_mo_ultimate_when_user_already_has_it(self):
        user = User.objects.create_user('test', 'test@test.com', 'password')
        premium = Generators.premium_subscription(user, 'AstroBin Premium')
        premium.expires = datetime(2020, 2, 16)
        premium.save()

        ultimate = Generators.premium_subscription(user, 'AstroBin Ultimate 2020+')
        ultimate.expires = date(2021, 3, 28)
        ultimate.save()


        self.client.login(username='test', password='password')

        response = self.client.post(
            reverse('astrobin_apps_premium.data_loss_compensation_request'),
            {
                'requested_compensation': '6_MO_ULTIMATE'
            })

        self.assertRedirects(
            response,
            reverse('astrobin_apps_premium.data_loss_compensation_request_success'),
            status_code=302,
            target_status_code=200)

        compensation_request = DataLossCompensationRequest.objects.get(user=user)
        self.assertEquals(compensation_request.requested_compensation, '6_MO_ULTIMATE')

        ultimate = get_object_or_None(UserSubscription, user=user, subscription__name='AstroBin Ultimate 2020+')

        self.assertIsNotNone(ultimate)
        self.assertTrue(ultimate.active)
        self.assertTrue(ultimate.cancelled)
        self.assertTrue(ultimate.expires > date(2021, 3, 28) + timedelta(days=179))
        self.assertTrue(ultimate.expires < date(2021, 3, 28) + timedelta(days=181))

        self.assertTrue(is_ultimate_2020(user))
