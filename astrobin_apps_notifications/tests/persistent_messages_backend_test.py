from django.contrib.auth.models import User
from django.test import TransactionTestCase
from notification.models import NoticeType
from persistent_messages.models import Message

from astrobin.tests.generators import Generators
from astrobin_apps_notifications.backends import PersistentMessagesBackend


class EmailBackendTest(TransactionTestCase):
    def setUp(self):
        self.notice_type = NoticeType.objects.get(label="test_notification")

    def test_deliver_with_shadow_ban(self):
        sender: User = Generators.user()
        user: User = Generators.user()

        user.userprofile.shadow_bans.add(sender.userprofile)

        PersistentMessagesBackend(1).deliver(user, sender, self.notice_type, {})

        self.assertFalse(Message.objects.exists())

    def test_deliver(self):
        sender: User = Generators.user()
        user: User = Generators.user()

        PersistentMessagesBackend(1).deliver(user, sender, self.notice_type, {})

        self.assertTrue(Message.objects.exists())
