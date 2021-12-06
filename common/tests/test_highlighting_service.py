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
        self.assertEquals('<span class="highlighted-text">Test</span>.', HighlightingService('Test.', 'Test').render_html())

    def test_render_html_single_term_URL(self):
        self.assertEquals(
            '<a href="https://www.test.com?foo=a%20test">test</a>',
            HighlightingService('<a href="https://www.test.com?foo=a%20test">test</a>', 'Test').render_html()
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
