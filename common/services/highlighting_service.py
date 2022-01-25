import math
import string

from django.utils.html import strip_tags
from precise_bbcode.templatetags.bbcode_tags import bbcode

from astrobin.settings.components.forum import SANITIZER_ALLOWED_TAGS


class HighlightingService:
    css_class = 'highlighted-text'
    html_tag = 'span'
    max_length = -1
    dialect = 'html'

    def __init__(self, text, terms, **kwargs):
        self.text = text
        self.terms = terms

        if 'max_length' in kwargs:
            self.max_length = int(kwargs['max_length'])

        if 'html_tag' in kwargs:
            self.html_tag = kwargs['html_tag']

        if 'css_class' in kwargs:
            self.css_class = kwargs['css_class']

        if 'dialect' in kwargs:
            self.dialect = kwargs['dialect']

    def render_html(self) -> str:
        if self.terms in (None, ''):
            return self.text

        if self.dialect == 'bbcode':
            result = bbcode(self.text)
        else:
            result = self.text

        result = strip_tags(result.replace('<br />', ' '))

        text_words = [
            word.translate(str.maketrans('', '', string.punctuation))
            for word in list(dict.fromkeys(result.split()))
        ]

        terms_words = [
            word.lower()
            for word in self.terms.split()
            if not word.startswith("-") and len(word) > 2 and word not in SANITIZER_ALLOWED_TAGS
        ]

        half_length = self.max_length / 2
        padding = max(self.max_length / 10, 20)
        first_match_index = int(max(
            min([result.lower().find(x.lower()) for x in self.terms.split() if not x.startswith('-')]) - padding,
            0
        ))
        last_match_index = int(min(
            max(
                [result.lower().find(x.lower()) for x in self.terms.split() if not x.startswith('-')]
            ) + padding,
            len(self.text)
        ))

        middle = (first_match_index + last_match_index) / 2

        if self.max_length > 0:
            start = max(min(math.floor(middle - half_length) - 1, first_match_index), 0)
            end = min(math.ceil(middle + max(half_length, last_match_index - first_match_index)), last_match_index)
        else:
            start = 0
            end = len(result)

        result = f'{"..." if start > 0 else ""}{result[start:end]}{"..." if end < len(result) else ""}'

        for word in text_words:
            if word.lower() in terms_words:
                result = result.replace(word, f'<{self.html_tag} class="{self.css_class}">{word}</{self.html_tag}>')

        return result
