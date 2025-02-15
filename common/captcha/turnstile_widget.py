from django import forms
from django.conf import settings


class TurnstileWidget(forms.Widget):
    def __init__(self, attrs=None):
        super().__init__(attrs)
        self.attrs = attrs or {}
        self.attrs['data-sitekey'] = settings.TURNSTILE_SITE_KEY

    def render(self, name, value, attrs=None, renderer=None):
        if settings.DEBUG or getattr(settings, 'TESTING', False):
            return ''  # Return empty string in test/debug mode

        attrs = attrs or {}
        final_attrs = self.build_attrs(self.attrs, attrs)
        return '''
            <div class="cf-turnstile" data-sitekey="{sitekey}" data-theme="dark"></div>
            <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
        '''.format(sitekey=final_attrs['data-sitekey'])

    def value_from_datadict(self, data, files, name):
        # Get the value from cf-turnstile-response instead of the field name
        return data.get('cf-turnstile-response')
