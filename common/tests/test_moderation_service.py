from django.contrib.auth.models import Group, User
from django.test import TestCase

from astrobin.tests.generators import Generators
from common.services.moderation_service import ModerationService


class ModerationServiceTest(TestCase):
    def test_auto_approve_astrobin_com(self):
        self.assertTrue(ModerationService.auto_approve(Generators.user(email='test@astrobin.com')))

    def test_auto_approve_highpointscientific_com(self):
        self.assertTrue(ModerationService.auto_approve(Generators.user(email='test@highpointscientific.com')))

    def test_do_not_auto_approve_anything_else(self):
        self.assertFalse(ModerationService.auto_approve(Generators.user(email='test@foobar123xyz.com')))

    def test_auto_approve_group(self):
        user: User = Generators.user(email='test@foo.com')

        self.assertFalse(ModerationService.auto_approve(user))

        group, created = Group.objects.get_or_create(name="auto_approve_content")
        group.user_set.add(user)

        self.assertTrue(ModerationService.auto_approve(user))
