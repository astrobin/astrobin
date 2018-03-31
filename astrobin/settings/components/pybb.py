PYBB_DEFAULT_TITLE = "AstroBin Forum"
PYBB_DEFAULT_FROM_EMAIL = "AstroBin Forum <noreply@astrobin.com>"
PYBB_NICE_URL = True
PYBB_PERMISSION_HANDLER = "astrobin.permissions.CustomForumPermissions"
PYBB_ATTACHMENT_ENABLE = False
PYBB_PROFILE_RELATED_NAME = 'userprofile'
PYBB_SMILES_PREFIX = 'astrobin/emoticons/'
PYBB_SMILES = {
    '&gt;_&lt;': 'mad.png',
    ':.(': 'sad.png',
    'o_O': 'smartass.png',
    '8)': 'sunglasses.png',
    ':D': 'grin.png',
    ':(': 'sad.png',
    ':O': 'surprised.png',
    '-_-': 'sorry.png',
    ':)': 'smile.png',
    ':P': 'tongue.png',
    ';)': 'blink.png',
    '&lt;3': 'love.png',
}
PYBB_TOPIC_PAGE_SIZE = 25
PYBB_FORUM_PAGE_SIZE = 50

def pybb_premoderation(user, post_content):
    # Paying members always approved
    from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import (
        is_lite, is_premium)
    if is_lite(user) or is_premium(user):
        return True

    # Users with sufficient index are always approved
    from django.conf import settings
    index = user.userprofile.get_scores()['user_scores_index']
    if index >= settings.MIN_INDEX_TO_LIKE:
        return True

    # Users that have had 5 messages approved before are always approved
    from pybb.models import Post
    posts = Post.objects.filter(user = user, on_moderation = False)
    if posts.count() >= 5:
        return True

    return False
PYBB_PREMODERATION = pybb_premoderation

SANITIZER_ALLOWED_TAGS = ['b', 'i', 'strong', 'em', 'a', 'img']
SANITIZER_ALLOWED_ATTRIBUTES = ['href', 'target', 'src']


