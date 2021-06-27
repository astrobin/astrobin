from annoying.functions import get_object_or_None
from precise_bbcode.bbcode.tag import BBCodeTag
from precise_bbcode.tag_pool import tag_pool

from astrobin.models import UserProfile


class QuoteBBCodeTag(BBCodeTag):
    name = 'quote'

    def render(self, value, option=None, parent=None):
        if option:
            username = option.replace('"', '')
            profile = get_object_or_None(UserProfile, user__username=username)
            if not profile:
                profile = get_object_or_None(UserProfile, real_name=username)
            if profile:
                return '<blockquote><a href="/users/{}">{}</a>:<br/>{}</blockquote>'.format(
                    profile.user.username,
                    profile.get_display_name(),
                    value
                )

        return '<blockquote>{}</blockquote>'.format(value)


tag_pool.register_tag(QuoteBBCodeTag)