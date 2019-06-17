# Django
from django.contrib.auth.models import User, Group
from django.test import TestCase
# Third party
from subscription.models import Subscription

# Rawdata
from rawdata.utils import *


class UtilsTest(TestCase):
    def test_subscription_validity(self):
        u = User.objects.create_user(
            username='test', email='test@test.com', password='password')
        g, created = Group.objects.get_or_create(name="rawdata")
        s, created = Subscription.objects.get_or_create(
            name="test_subscription",
            price=1,
            group=g,
            category="rawdata")
        us, created = UserSubscription.objects.get_or_create(
            user=u,
            subscription=s)

        us.subscribe()

        self.assertEqual(rawdata_user_get_subscription(u), us)
        self.assertEqual(rawdata_user_get_valid_subscription(u), us)
        self.assertEqual(rawdata_user_has_subscription(u), True)
        self.assertEqual(rawdata_user_has_valid_subscription(u), True)
        self.assertEqual(rawdata_user_has_invalid_subscription(u), False)

        us.delete()
        s.delete()
        g.delete()
        u.delete()
