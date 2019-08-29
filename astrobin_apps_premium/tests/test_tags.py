import datetime

from django.contrib.auth.models import Group, User
from django.test import TestCase
from subscription.models import Subscription

from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import is_offer, has_valid_premium_offer


class TagsTest(TestCase):
    def test_has_valid_premium_offer(self):
        user = User.objects.create(username="foo", password="foo")

        self.assertFalse(has_valid_premium_offer(user))

        user.userprofile.premium_offer = "premium_offer_discount_20"

        self.assertFalse(has_valid_premium_offer(user))

        user.userprofile.premium_offer_expiration = datetime.datetime.now() - datetime.timedelta(hours=1)

        self.assertFalse(has_valid_premium_offer(user))

        user.userprofile.premium_offer_expiration = datetime.datetime.now() + datetime.timedelta(hours=1)

        self.assertTrue(has_valid_premium_offer(user))

        user.delete()

    def test_is_offer(self):
        group = Group.objects.create(name="test")
        subscription = Subscription.objects.create(
            name="Test", price=1, group=group, category="foo")

        self.assertFalse(is_offer(subscription))

        subscription.category = "premium_offer_discount_20"

        self.assertTrue(is_offer(subscription))

        group.delete()
        subscription.delete()
