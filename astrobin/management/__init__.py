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
        2,
    ),
    (
        'follow_success',
        _('Following a user was successful'),
        '',
        1,
    ),
    (
        'unfollow_success',
        _('Unfollowing a user was successful'),
        '',
        1,
    ),
    (
        'new_image',
        _('New image from a user you follow'),
        '',
        2,
    ),
    (
        'attention_request',
        _('Image brought to your attention'),
        '',
        2,
    ),
    (
        'new_image_revision',
        _('New image revision from a user you follow'),
        '',
        2,
    ),
    (
        'image_ready',
        _('Your image is ready'),
        '',
        1,
    ),
    (
        'image_solved',
        _('Your image was plate-solved'),
        '',
        1,
    ),
    (
        'image_not_solved',
        _('Your image could not be plate-solved'),
        '',
        1,
    ),
    (
        'request_fulfilled',
        _('Your request was fulfilled'),
        '',
        1,
    ),
    (
        'image_deleted',
        _('Your image was deleted'),
        '',
        1,
    ),
    (
        'new_blog_entry',
        _('AstroBin has published a new blog entry'),
        '',
        1,
    ),
    (
        'lacking_data_reminder',
        _("You have some images that are lacking data"),
        '',
        1,
    ),
    (
        'new_comment',
        _("Your image received a new comment"),
        '',
        2,
    ),
    (
        'new_comment_reply',
        _("There was a reply to your comment"),
        '',
        2,
    ),
    (
        'new_bookmark',
        _("Your image was bookmarked"),
        '',
        2,
    ),
    (
        'new_like',
        _("Your image was liked"),
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
    (
        'new_gear_discussion',
        _("New discussion about a gear item you own"),
        '',
        2,
    ),
    (
        'new_gear_review',
        _("New review of a gear item you own"),
        '',
        2,
    ),
    (
        'rawdata_posted_to_pool',
        _("New data posted to public pool"),
        '',
        2,
    ),
    (
        'rawdata_posted_image_to_public_pool',
        _("New image posted to public data pool"),
        '',
        2,
    ),
    (
        'rawdata_posted_to_private_folder',
        _("New data posted to shared private folder"),
        '',
        2,
    ),
    (
        'rawdata_posted_image_to_private_folder',
        _("New image posted to shared private folder"),
        '',
        2,
    ),
    (
        'rawdata_invited_to_private_folder',
        _("You are invited to a shared private folder"),
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
                                        default = notice_type[3])


signals.post_syncdb.connect(create_notice_types, sender=notification)

