from annoying.functions import get_object_or_None
from django.core.exceptions import MultipleObjectsReturned
from django.utils.encoding import smart_str
from precise_bbcode.bbcode.tag import BBCodeTag
from precise_bbcode.tag_pool import tag_pool

from astrobin.models import UserProfile


class QuoteBBCodeTag(BBCodeTag):
    name = 'quote'

    class Options:
        strip = True

    def render(self, value, option=None, parent=None):
        content = smart_str(value)

        if option:
            username = smart_str(option).replace('"', '')
            profile = get_object_or_None(UserProfile, user__username=username)
            if not profile:
                try:
                    profile = get_object_or_None(UserProfile, real_name=username)
                except MultipleObjectsReturned:
                    return '<blockquote><em>{}</em>:<br/>{}</blockquote>'.format(
                        username,
                        content
                    )
            if profile:
                return '<blockquote><a href="/users/{}">{}</a>:<br/>{}</blockquote>'.format(
                    profile.user.username,
                    smart_str(profile.get_display_name()),
                    content
                )

        return '<blockquote>{}</blockquote>'.format(content)


tag_pool.register_tag(QuoteBBCodeTag)
