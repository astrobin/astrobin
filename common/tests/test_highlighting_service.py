from django.test import TestCase

from common.services.highlighting_service import HighlightingService


class HighlightingServiceTest(TestCase):
    def test_render_html_none(self):
        self.assertEquals('Test', HighlightingService('Test', None).render_html())

    def test_render_html_empty(self):
        self.assertEquals('Test', HighlightingService('Test', '').render_html())

    def test_render_html_term_not_found(self):
        self.assertEquals('Test', HighlightingService('Test', 'Foo').render_html())

    def test_render_html_term_too_short(self):
        self.assertEquals('Te', HighlightingService('Te', 'Te').render_html())

    def test_render_html_term_sanitized_HTML_tag(self):
        self.assertEquals('strong', HighlightingService('strong', 'strong').render_html())

    def test_render_html_single_term(self):
        self.assertEquals('<span class="highlighted-text">Test</span>', HighlightingService('Test', 'Test').render_html())

    def test_render_html_single_term_ignore_punctuation(self):
        self.assertEquals(
            '<span class="highlighted-text">Test</span>.',
            HighlightingService('Test.', 'Test', escape=False).render_html()
        )

    def test_render_html_single_term_URL_is_not_stripped(self):
        self.assertEquals(
            '<a href="https://www.test.com?foo=a%20test"><span class="highlighted-text">test</span></a>',
            HighlightingService(
                '<a href="https://www.test.com?foo=a%20test">test</a>',
                'Test',
                escape=False
            ).render_html()
        )

    def test_render_html_no_terms(self):
        self.assertEquals(
            'Test test',
            HighlightingService('Test test', '').render_html()
        )

    def test_render_html_excluded_term(self):
        self.assertEquals(
            'Test test',
            HighlightingService('Test test', '-foo').render_html()
        )

    def test_render_html_single_term_multiple_matches(self):
        self.assertEquals(
            '<span class="highlighted-text">Test</span> <span class="highlighted-text">test</span>',
            HighlightingService('Test test', 'Test').render_html()
        )

    def test_render_html_multiple_terms_no_matches(self):
        self.assertEquals('Test', HighlightingService('Test', 'Foo bar').render_html())

    def test_render_html_multiple_terms_one_match(self):
        self.assertEquals(
            '<span class="highlighted-text">Test</span>',
            HighlightingService('Test', 'Test bar').render_html()
        )

        self.assertEquals(
            '<span class="highlighted-text">Test</span>',
            HighlightingService('Test', 'Bar Test').render_html()
        )

    def test_render_html_multiple_terms_multiple_matches(self):
        self.assertEquals(
            '<span class="highlighted-text">Test</span> is <span class="highlighted-text">fine</span>',
            HighlightingService('Test is fine', 'Test fine').render_html()
        )

    def test_render_html_single_term_max_length_too_short(self):
        # This max_length is ignored because 20 is the minimum.
        self.assertEquals(
            'this <span class="highlighted-text">test</span> rules',
            HighlightingService('this test rules', 'test', max_length=2).render_html()
        )

    def test_render_html_single_term_max_length(self):
        text = 'This message is a very, very long message of test that will cause the appearance of ellipses'
        self.assertEquals(
            '...ery long message of <span class="highlighted-text">test</span> that will cause...',
            HighlightingService(text, 'test', max_length=20).render_html()
        )

    def test_render_html_single_term_max_length_larger_than_text(self):
        text = 'This message is a very, very long message of test but will not cause the appearance of ellipses'
        self.assertEquals(
            'This message is a very, very long message of <span class="highlighted-text">test</span> but will not '
            'cause the appearance of ellipses',
            HighlightingService(text, 'test', max_length=500).render_html()
        )

    def test_render_html_single_term_max_length_but_term_not_found(self):
        text = 'This message is a very very long message of test that will cause the appearance of ellipses'
        self.assertEquals(
            'This message is a v...',
            HighlightingService(text, 'foo', max_length=20).render_html()
        )

    def test_render_html_single_term_max_length_short_text(self):
        self.assertEquals(
            'hello <span class="highlighted-text">test</span>',
            HighlightingService('hello test', 'test', max_length=50).render_html()
        )
