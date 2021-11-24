import string

from astrobin.settings.components.forum import SANITIZER_ALLOWED_TAGS


class HighlightingService:
    def __init__(self, text, terms):
        self.text = text
        self.terms = terms

    def render_html(self) -> str:
        html = self.text

        if self.terms not in (None, ''):
            text_words = [
                word.translate(str.maketrans('', '', string.punctuation))
                for word in list(dict.fromkeys(self.text.split()))
            ]

            terms_words = [
                word.lower()
                for word in self.terms.split()
                if not word.startswith("-") and len(word) > 2 and word not in SANITIZER_ALLOWED_TAGS
            ]

            for word in text_words:
                if word.lower() in terms_words:
                    html = html.replace(word, f'<span class="highlighted-text">{word}</span>')

        return html
