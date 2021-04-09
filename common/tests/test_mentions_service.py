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
        text = "Hello [url=https://www.astrobin.com/users/foo/]@Foo Smith[/url] and [url=https://www.astrobin.com/users/bar/]@Bar Test[/url]"
        self.assertEquals(["foo", "bar"], MentionsService.get_mentions(text))

    def test_get_mentions_two_mentions_multiline(self):
        text = "Hello [url=https://www.astrobin.com/users/foo/]@Foo Smith[/url]\nHello [url=https://www.astrobin.com/users/bar/]@Bar Test[/url]"
        self.assertEquals(["foo", "bar"], MentionsService.get_mentions(text))

    def test_get_mentions_unique_mentions(self):
        text = "Hello [url=https://www.astrobin.com/users/foo/]@Foo Smith[/url] and [url=https://www.astrobin.com/users/foo/]@Foo Smith[/url]"
        self.assertEquals(["foo"], MentionsService.get_mentions(text))
