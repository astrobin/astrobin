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
