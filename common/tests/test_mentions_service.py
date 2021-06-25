from django.test import TestCase

from common.services.mentions_service import MentionsService


class MentionsServiceTest(TestCase):
    def test_get_mentions_empty_string(self):
        self.assertEquals([], MentionsService.get_mentions(""))

    def test_get_mentions_no_mentions(self):
        self.assertEquals([], MentionsService.get_mentions("hello"))

    def test_get_mentions_one_mention(self):
        text = "Hello [url=https://www.astrobin.com/users/foo/]@Foo Bar[/url]"
        self.assertEquals(["foo"], MentionsService.get_mentions(text))

    def test_get_mentions_http(self):
        text = "Hello [url=http://www.astrobin.com/users/foo/]@Foo Bar[/url]"
        self.assertEquals(["foo"], MentionsService.get_mentions(text))

    def test_get_mentions_no_www(self):
        text = "Hello [url=https://astrobin.com/users/foo/]@Foo Bar[/url]"
        self.assertEquals(["foo"], MentionsService.get_mentions(text))

    def test_get_mentions_localhost_and_port(self):
        text = "Hello [url=http://localhost:8084/users/foo/]@Foo Bar[/url]"
        self.assertEquals(["foo"], MentionsService.get_mentions(text))

    def test_get_mentions_two_mentions(self):
        text = "Hello [url=https://www.astrobin.com/users/foo/]@Foo Smith[/url] and " \
               "[url=https://www.astrobin.com/users/bar/]@Bar Test[/url]"
        mentions = MentionsService.get_mentions(text)
        self.assertTrue("foo" in mentions)
        self.assertTrue("bar" in mentions)

    def test_get_mentions_two_mentions_multiline(self):
        text = "Hello [url=https://www.astrobin.com/users/foo/]@Foo Smith[/url]\nHello " \
               "[url=https://www.astrobin.com/users/bar/]@Bar Test[/url]"
        self.assertEquals(["foo", "bar"], MentionsService.get_mentions(text))

    def test_get_mentions_unique_mentions(self):
        text = "Hello [url=https://www.astrobin.com/users/foo/]@Foo Smith[/url] and " \
               "[url=https://www.astrobin.com/users/foo/]@Foo Smith[/url]"
        self.assertEquals(["foo"], MentionsService.get_mentions(text))

    def test_get_mentions_one_quote(self):
        text = "[quote=\"foo\"]Test message[/quote]"
        self.assertEquals(["foo"], MentionsService.get_mentions(text))

    def test_get_mentions_two_quotes(self):
        text = "[quote=\"foo\"]Test message[/quote] OK [quote=\"foo\"]Test message[/quote]"
        self.assertEquals(["foo"], MentionsService.get_mentions(text))

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
        self.assertEquals([], MentionsService.get_mentions(text))

    def test_get_mentions_quote_and_mention_same_user(self):
        text = "[quote=\"foo\"]Test message[/quote] Hello [url=https://www.astrobin.com/users/foo/]@Foo Bar[/url]"
        self.assertEquals(["foo"], MentionsService.get_mentions(text))

    def test_get_mentions_quote_and_mention_unique_users(self):
        text = "[quote=\"bar\"]Test message[/quote] Hello [url=https://www.astrobin.com/users/foo/]@Foo Bar[/url]"
        mentions = MentionsService.get_mentions(text)
        self.assertTrue("foo" in mentions)
        self.assertTrue("bar" in mentions)
