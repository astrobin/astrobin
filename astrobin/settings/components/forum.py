PYBB_MARKUP_ENGINES_PATHS = {
    'bbcode': 'astrobin.bbcode_parser.AstroBinBBCodeParser',
    'markdown': 'pybb.markup.markdown.MarkdownParser'
}
PYBB_DISABLE_NOTIFICATIONS = True
PYBB_BODY_CLEANERS = []
PYBB_DEFAULT_TITLE = "AstroBin Forum"
PYBB_DEFAULT_FROM_EMAIL = "AstroBin Forum <noreply@astrobin.com>"
PYBB_NICE_URL = True
PYBB_PERMISSION_HANDLER = "astrobin.permissions.CustomForumPermissions"
PYBB_ATTACHMENT_ENABLE = False
PYBB_PROFILE_RELATED_NAME = 'userprofile'
PYBB_SMILES_PREFIX = 'astrobin/emoticons/'
PYBB_SMILES = {
    '&gt;_&lt;': 'angry.png',
    ':.(': 'sad.png',
    'o_O': 'smart.png',
    '8-)': 'cool.png',
    ':D': 'laughing.png',
    ':(': 'sad.png',
    ':O': 'surprised.png',
    '-_-': 'sad-2.png',
    ':)': 'happy.png',
    ':P': 'tongue.png',
    '&lt;3': 'in-love.png',

    ':angel:': 'angel.png',
    ':angry-1:': 'angry-1.png',
    ':angry:': 'angry.png',
    ':arrogant:': 'arrogant.png',
    ':bored:': 'bored.png',
    ':confused:': 'confused.png',
    ':cool-1:': 'cool-1.png',
    ':cool:': 'cool.png',
    ':crying-1:': 'crying-1.png',
    ':crying-2:': 'crying-2.png',
    ':crying:': 'crying.png',
    ':cute:': 'cute.png',
    ':embarrassed:': 'embarrassed.png',
    ':emoji:': 'emoji.png',
    ':greed:': 'greed.png',
    ':happy-1:': 'happy-1.png',
    ':happy-2:': 'happy-2.png',
    ':happy-3:': 'happy-3.png',
    ':happy-4:': 'happy-4.png',
    ':happy-5:': 'happy-5.png',
    ':happy-6:': 'happy-6.png',
    ':happy-7:': 'happy-7.png',
    ':happy:': 'happy.png',
    ':in-love:': 'in-love.png',
    ':kiss-1:': 'kiss-1.png',
    ':kiss:': 'kiss.png',
    ':laughing-1:': 'laughing-1.png',
    ':laughing-2:': 'laughing-2.png',
    ':laughing:': 'laughing.png',
    ':muted:': 'muted.png',
    ':nerd:': 'nerd.png',
    ':sad-1:': 'sad-1.png',
    ':sad-2:': 'sad-2.png',
    ':sad:': 'sad.png',
    ':scare:': 'scare.png',
    ':serious:': 'serious.png',
    ':shocked:': 'shocked.png',
    ':sick:': 'sick.png',
    ':sleepy:': 'sleepy.png',
    ':smart:': 'smart.png',
    ':surprised-1:': 'surprised-1.png',
    ':surprised-2:': 'surprised-2.png',
    ':surprised-3:': 'surprised-3.png',
    ':surprised-4:': 'surprised-4.png',
    ':surprised:': 'surprised.png',
    ':suspicious:': 'suspicious.png',
    ':tongue:': 'tongue.png',
    ':vain:': 'vain.png',
    ':wink-1:': 'wink-1.png',
    ':wink:': 'wink.png'
}
PYBB_TOPIC_PAGE_SIZE = 25
PYBB_FORUM_PAGE_SIZE = 50

def pybb_premoderation(user, post_content, forum):
    if user.is_superuser:
        return True

    # Everybody gets moderated in these forums
    if forum and forum.name in ('Anything goes', 'Other'):
        return False

    from common.services.moderation_service import ModerationService

    if ModerationService.auto_enqueue_for_moderation(user):
        return False

    if ModerationService.auto_approve(user):
        return True

    # Paying members always approved
    from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import is_free
    from astrobin_apps_premium.services.premium_service import PremiumService

    valid_subscription = PremiumService(user).get_valid_usersubscription()
    if not is_free(valid_subscription):
        return True

    from pybb.models import Post

    # Users that have not had some posts approved before are always rejected
    return Post.objects.filter(user=user, on_moderation=False).count() >= 3

PYBB_PREMODERATION = pybb_premoderation

SANITIZER_ALLOWED_TAGS = ['b', 'i', 'strong', 'em', 'a', 'img', 'br', 'span', 'p', 'ul', 'li', 'ol', 'pre', 'code']
SANITIZER_ALLOWED_ATTRIBUTES = ['href', 'target', 'src', 'class', 'alt', 'width', 'height', 'rel', 'style']
SANITIZER_ALLOWED_STYLES = ['font-size']

