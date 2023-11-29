import math
import string

import regex
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from precise_bbcode.templatetags.bbcode_tags import bbcode

from astrobin.settings.components.forum import SANITIZER_ALLOWED_TAGS


class HighlightingService:
    css_class = 'highlighted-text'
    html_tag = 'span'
    max_length = -1
    dialect = 'html'
    allow_lists = 'True'

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

        if 'allow_lists' in kwargs:
            self.allow_lists = kwargs['allow_lists']

    def render_html(self) -> str:
        if self.dialect == 'bbcode':
            result = bbcode(self.text)
        else:
            result = self.text

        if self.terms not in (None, ''):
            text_words = [
                word.translate(str.maketrans('', '', string.punctuation))
                for word in list(dict.fromkeys(strip_tags(result).split()))
            ]

            terms_words = [
                word.lower()
                for word in self.terms.split()
                if not word.startswith("-") and len(word) > 2 and word not in SANITIZER_ALLOWED_TAGS
            ]

            if len(terms_words) > 0:
                half_length = self.max_length / 2
                padding = max(self.max_length / 10, 20)
                first_match_index = int(
                    max(
                        min(
                            [result.lower().find(x.lower()) for x in self.terms.split() if not x.startswith('-')]
                        ) - padding,
                        0
                    )
                )
                last_match_index = int(
                    min(
                        max(
                            [result.lower().find(x.lower()) for x in self.terms.split() if not x.startswith('-')]
                        ) + padding,
                        len(self.text)
                    )
                )

                middle = (first_match_index + last_match_index) / 2

                if self.max_length > 0:
                    start = max(min(math.floor(middle - half_length) - 1, first_match_index), 0)
                    end = min(
                        math.ceil(middle + max(half_length, last_match_index - first_match_index)), last_match_index
                    )
                else:
                    start = 0
                    end = len(result)

                result = f'{"..." if start > 0 else ""}{result[start:end]}{"..." if end < len(result) else ""}'

                for word in text_words:
                    if word.lower() in terms_words:
                        result = regex.sub(
                            f'\<(?:[^<>]++|(?0))++\>(*SKIP)(*F)|{word}',
                            f'<{self.html_tag} class="{self.css_class}">{word}</{self.html_tag}>',
                            result
                        )

        from common.templatetags.common_tags import strip_html

        if self.allow_lists == 'True':
            allowed_tags = SANITIZER_ALLOWED_TAGS
        else:
            # If we don't allow lists, we need to remove the <li> tags. We do this because search results use lists and
            # the layout breaks if we don't remove them.
            allowed_tags = SANITIZER_ALLOWED_TAGS.copy()
            allowed_tags.remove('ul')
            allowed_tags.remove('ol')
            allowed_tags.remove('li')

            result = result \
                .replace('<li>', '<p>') \
                .replace('</li>', '</p>') \
                .replace('<ul>', '') \
                .replace('</ul>', '') \
                .replace('<ol>', '') \
                .replace('</ol>', '')

        return mark_safe(
            strip_html('<br />'.join(result.splitlines()), allowed_tags=allowed_tags)
        )
