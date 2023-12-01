from django.test import TestCase
from notification.models import NoticeSetting, NoticeType

from astrobin.tests.generators import Generators
from common.services.mentions_service import MentionsService


class MentionsServiceTest(TestCase):
    def test_get_mentions_empty_string(self):
        self.assertEqual([], MentionsService.get_mentions(""))

    def test_get_mentions_no_mentions(self):
        self.assertEqual([], MentionsService.get_mentions("hello"))

    def test_get_mentions_one_mention(self):
        text = "Hello [url=https://www.astrobin.com/users/foo/]@Foo Bar[/url]"
        self.assertEqual(["foo"], MentionsService.get_mentions(text))

    def test_get_mentions_http(self):
        text = "Hello [url=http://www.astrobin.com/users/foo/]@Foo Bar[/url]"
        self.assertEqual(["foo"], MentionsService.get_mentions(text))

    def test_get_mentions_no_www(self):
        text = "Hello [url=https://astrobin.com/users/foo/]@Foo Bar[/url]"
        self.assertEqual(["foo"], MentionsService.get_mentions(text))

    def test_get_mentions_localhost_and_port(self):
        text = "Hello [url=http://localhost:8084/users/foo/]@Foo Bar[/url]"
        self.assertEqual(["foo"], MentionsService.get_mentions(text))

    def test_get_mentions_two_mentions(self):
        text = "Hello [url=https://www.astrobin.com/users/foo/]@Foo Smith[/url] and " \
               "[url=https://www.astrobin.com/users/bar/]@Bar Test[/url]"
        mentions = MentionsService.get_mentions(text)
        self.assertTrue("foo" in mentions)
        self.assertTrue("bar" in mentions)

    def test_get_mentions_two_mentions_multiline(self):
        text = "Hello [url=https://www.astrobin.com/users/foo/]@Foo Smith[/url]\nHello " \
               "[url=https://www.astrobin.com/users/bar/]@Bar Test[/url]"
        mentions = MentionsService.get_mentions(text)
        self.assertTrue("foo" in mentions)
        self.assertTrue("bar" in mentions)

    def test_get_mentions_unique_mentions(self):
        text = "Hello [url=https://www.astrobin.com/users/foo/]@Foo Smith[/url] and " \
               "[url=https://www.astrobin.com/users/foo/]@Foo Smith[/url]"
        self.assertEqual(["foo"], MentionsService.get_mentions(text))

    def test_get_mentions_one_quote(self):
        text = "[quote=\"foo\"]Test message[/quote]"
        self.assertEqual(["foo"], MentionsService.get_mentions(text))

    def test_get_mentions_two_quotes(self):
        text = "[quote=\"foo\"]Test message[/quote] OK [quote=\"foo\"]Test message[/quote]"
        self.assertEqual(["foo"], MentionsService.get_mentions(text))

    def test_get_mentions_two_unique_quotes(self):
        text = "[quote=\"foo\"]Test message[/quote] OK [quote=\"bar\"]Test message[/quote]"
        mentions = MentionsService.get_mentions(text)
        self.assertTrue("foo" in mentions)
        self.assertTrue("bar" in mentions)

    def test_get_mentions_nested_quotes_only_mentions_outer(self):
        text = "[quote=\"foo\"][quote=\"bar\"]2[/quote]1[/quote]"
        mentions = MentionsService.get_mentions(text)
        self.assertTrue("foo" in mentions)
        self.assertFalse("bar" in mentions)

        text = "[quote=\"foo\"][quote=\"bar\"][quote=\"tar\"]3[/quote]2[/quote]1[/quote]"
        mentions = MentionsService.get_mentions(text)
        self.assertTrue("foo" in mentions)
        self.assertFalse("bar" in mentions)
        self.assertFalse("tar" in mentions)

    def test_get_mentions_quote_without_user(self):
        text = "[quote]Test message[/url]"
        self.assertEqual([], MentionsService.get_mentions(text))

    def test_get_mentions_quote_with_real_name_and_username(self):
        text = "[quote=\"Mr Fooish (foo)\"]Test message[/quote]"
        self.assertEqual(["foo"], MentionsService.get_mentions(text))

    def test_get_mentions_quote_and_mention_same_user(self):
        text = "[quote=\"foo\"]Test message[/quote] Hello [url=https://www.astrobin.com/users/foo/]@Foo Bar[/url]"
        self.assertEqual(["foo"], MentionsService.get_mentions(text))

    def test_get_mentions_quote_and_mention_unique_users(self):
        text = "[quote=\"bar\"]Test message[/quote] Hello [url=https://www.astrobin.com/users/foo/]@Foo Bar[/url]"
        mentions = MentionsService.get_mentions(text)
        self.assertTrue("foo" in mentions)
        self.assertTrue("bar" in mentions)

    def test_get_mentioned_users_with_notification_enabled_no_users(self):
        self.assertEqual([], MentionsService.get_mentioned_users_with_notification_enabled(
            [], 'new_forum_post_mention'))

    def test_get_mentioned_users_with_notification_enabled_no_users_with_notifications_enabled(self):
        user = Generators.user()
        self.assertEqual([], MentionsService.get_mentioned_users_with_notification_enabled(
            [user.username], 'new_forum_post_mention'))

    def test_get_mentioned_users_with_notification_enabled_users_with_notifications_enabled(self):
        user = Generators.user()
        notice_type = NoticeType.objects.create(
            label='new_forum_post_mention',
            display='',
            description='',
            default=2)
        NoticeSetting.for_user(user, notice_type, 1)
        self.assertEqual(
            [user],
            MentionsService.get_mentioned_users_with_notification_enabled([user.username], 'new_forum_post_mention'))

    def test_get_mentioned_users_with_notification_enabled_users_with_notifications_enabled_using_real_name(self):
        user = Generators.user()
        user.userprofile.real_name = "Foo"
        user.userprofile.save()
        notice_type = NoticeType.objects.create(
            label='new_forum_post_mention',
            display='',
            description='',
            default=2
        )
        NoticeSetting.for_user(user, notice_type, 1)
        self.assertEqual(
            [user],
            MentionsService.get_mentioned_users_with_notification_enabled(
                [user.userprofile.real_name], 'new_forum_post_mention'))
