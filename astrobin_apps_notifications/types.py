from django.utils.translation import ugettext_lazy as _

# Fields:
# 0 - notice label
# 1 - display name
# 2 - description
# 3 - default: if value >= 2, send e-mail by default
NOTICE_TYPES = (
    (
        'test_notification',
        'Test notification',
        '',
        2
    ),
    (
        'new_follower',
        _('You have a new follower'),
        '',
        2,
    ),
    (
        'new_image',
        _('New image from a user you follow'),
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
        'new_blog_entry',
        'AstroBin has published a new blog entry',
        '',
        1,
    ),
    (
        'new_comment',
        _('Your image received a new comment'),
        '',
        2,
    ),
    (
        'new_comment_reply',
        _('There was a reply to your comment'),
        '',
        2,
    ),
    (
        'new_bookmark',
        _('Your image was bookmarked'),
        '',
        2,
    ),
    (
        'new_like',
        _('Your image was liked'),
        '',
        2,
    ),
    (
        'new_image_from_gear',
        _('New image with some gear you follow'),
        '',
        2,
    ),
    (
        'new_image_of_subject',
        _('New image of a subject you follow'),
        '',
        2,
    ),
    (
        'api_key_request_approved',
        _('Your API Key request has been approved'),
        '',
        2,
    ),
    (
        'new_gear_discussion',
        _('New discussion about a gear item you own'),
        '',
        2,
    ),
    (
        'new_gear_review',
        _('New review of a gear item you own'),
        '',
        2,
    ),
    (
        'user_joined_public_group',
        _('A user you follow joined a public group'),
        '',
        2,
    ),
    (
        'new_group_invitation',
        _('You are invited to a group'),
        '',
        2,
    ),
    (
        'new_group_join_request',
        _('A user requested to join a group you moderate'),
        '',
        2,
    ),
    (
        'group_join_request_approved',
        _('A group moderator approved your request to join'),
        '',
        2,
    ),
    (
        'group_join_request_rejected',
        _('A group moderator rejected your request to join'),
        '',
        2,
    ),
    (
        'new_public_group_created',
        _('A user you follow created a new public group'),
        '',
        2,
    ),
    (
        'new_topic_in_group',
        _('New forum topic in a group you are a member of'),
        '',
        2,
    ),
    (
        'received_email',
        _('You have received a new private message'),
        '',
        2
    ),
    (
        'expiring_subscription',
        _('Your premium subscription will expire in one week'),
        '',
        2
    ),
    (
        'expired_subscription',
        _('Your premium subscription has just expired'),
        '',
        2
    ),
    (
        'expiring_subscription_autorenew',
        _('Your subscription will be renewed in one week'),
        '',
        2
    ),
    (
        'missing_data_source',
        _('You have images with a missing "Data source"'),
        '',
        2
    ),
    (
        'missing_remote_source',
        _('You have images with a missing "Remote source"'),
        '',
        2
    )
)
