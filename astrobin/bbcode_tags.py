import re

from annoying.functions import get_object_or_None
from django.core.exceptions import MultipleObjectsReturned
from precise_bbcode.bbcode.tag import BBCodeTag
from precise_bbcode.tag_pool import TagAlreadyCreated, tag_pool

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


class SizeBBCodeTag(BBCodeTag):
    name = 'size'

    class Options:
        strip = True

    def render(self, value, option=None, parent=None):
        content = str(value)
        size = str(option).replace('"', '')

        # Check if the size is a valid number
        if not size.isdigit():
            return content

        size = int(size)
        if size <= 50:
            size = '.5rem'
        elif size <= 75:
            size = '.75rem'
        elif size <= 100:
            size = '1rem'
        elif size <= 150:
            size = '1.5rem'
        else:
            size = '2rem'

        return f'<span style="font-size: {size}">{content}</span>'


try:
    tag_pool.register_tag(QuoteBBCodeTag)
    tag_pool.register_tag(CodeBBCodeTag)
    tag_pool.register_tag(PreBBCodeTag)
    tag_pool.register_tag(SizeBBCodeTag)
except TagAlreadyCreated:
    pass
