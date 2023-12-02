import re

from annoying.functions import get_object_or_None
from django.core.exceptions import MultipleObjectsReturned
from precise_bbcode.bbcode.tag import BBCodeTag
from precise_bbcode.tag_pool import tag_pool

from astrobin.models import UserProfile


class QuoteBBCodeTag(BBCodeTag):
    name = 'quote'

    class Options:
        strip = True

    def render(self, value, option=None, parent=None):
        content = str(value)

        if option:
            username = str(option).replace('"', '')

            # match in case the format is "display name (username)"
            match = re.match(r'(.*) \((.*)\)', username)
            if match:
                username = match.group(2)
                profile = get_object_or_None(UserProfile, user__username=username)
            else:
                try:
                    profile = get_object_or_None(UserProfile, real_name=username)
                except MultipleObjectsReturned:
                    return '<blockquote><em>{}</em>:<br/>{}</blockquote>'.format(
                        username,
                        content
                    )

            if profile:
                return '<blockquote><a href="/users/{}/">{}</a>:<br/>{}</blockquote>'.format(
                    profile.user.username,
                    str(profile.get_display_name()),
                    content
                )

        return '<blockquote>{}</blockquote>'.format(content)


class CodeBBCodeTag(BBCodeTag):
    name = 'code'

    class Options:
        strip = True

    def render(self, value, option=None, parent=None):
        content = str(value)

        if option:
            klass = str(option).replace('"', '')
            if klass:
                return f'<code class="{klass}">{content}</code>'

        return f'<code>{content}</code>'


class PreBBCodeTag(BBCodeTag):
    name = 'pre'

    class Options:
        strip = True

    def render(self, value, option=None, parent=None):
        content = str(value)
        return f'<pre>{content}</pre>'


tag_pool.register_tag(QuoteBBCodeTag)
tag_pool.register_tag(CodeBBCodeTag)
tag_pool.register_tag(PreBBCodeTag)
