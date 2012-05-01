from django.conf import settings
from django.db.models import signals
from notification import models as notification

def _(s): return s

# Fields:
# 0 - notice label
# 1 - display name
# 2 - description
# 3 - default: if value >= 2, send e-mail by default
NOTICE_TYPES = (
    (
        'new_follower',
        _('You have a new follower'),
        '',
        2
    ),
    (
        'follow_success',
        _('Following a user was successful'),
        '',
        0
    ),
    (
        'unfollow_success',
        _('Unfollowing a user was successful'),
        '',
        0
    ),
    (
        'new_image',
        _('New image from a user you follow'),
        '',
        2
    ),
    (
        'attention_request',
        _('Image brought to your attention'),
        '',
        2
    ),
    (
        'new_image_revision',
        _('New image revision from a user you follow'),
        '',
        2
    ),
    (
        'image_ready',
        _('Your image is ready'),
        '',
        0
    ),
    (
        'image_solved',
        _('Your image was plate-solved'),
        '',
        2
    ),
    (
        'image_not_solved',
        _('Your image could not be plate-solved'),
        '',
        2
    ),
    (
        'request_fulfilled',
        _('Your request was fulfilled'),
        '',
        2
    ),
    (
        'image_deleted',
        _('Your image was deleted'),
        '',
        0
    ),
    (
        'new_blog_entry',
        _('AstroBin has published a new blog entry'),
        '',
        0
    ),
    (
        'messier_nomination',
        _("Nomination for the Messier Marathon"),
        '',
        2
    ),
    (
        'messier_top_nomination',
        _("Top Nomination for the Messier Marathon"),
        '',
        2
    ),
    (
        'lacking_data_reminder',
        _("You have some images that are lacking data"),
        '',
        0
    ),
    (
        'new_comment',
        _("Your image received a new comment"),
        '',
        2
    ),
    (
        'new_comment_reply',
        _("There was a reply to your comment"),
        '',
        2
    ),
    (
        'new_favorite',
        _("Your image was favorited"),
        '',
        2,
    ),
    (
        'new_image_from_gear',
        _("New image with some gear you follow"),
        '',
        2,
    ),
    (
        'new_image_of_subject',
        _("New image of a subject you follow"),
        '',
        2,
    ),
    (
        'api_key_request_approved',
        _("Your API Key request has been approved"),
        '',
        2,
    ),
)


def create_notice_types(app, created_models, verbosity, **kwargs):
    for notice_type in NOTICE_TYPES:
        print "Creating notice: %s" % notice_type[0]
        notification.create_notice_type(notice_type[0],
                                        notice_type[1],
                                        notice_type[2],
                                        notice_type[3])


signals.post_syncdb.connect(create_notice_types, sender=notification)

