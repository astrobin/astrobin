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
        'image_solved_advanced',
        _('Your image was plate-solved (advanced)'),
        '',
        1,
    ),
    (
        'image_not_solved_advanced',
        _('Your image could not be plate-solved (advanced)'),
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
        'new_comment_to_edit_proposal',
        _('Your edit proposal received a new comment'),
        '',
        2,
    ),
    (
        'new_comment_to_scheduled_iotd',
        _('Your scheduled IOTD received a new comment'),
        '',
        2,
    ),
    (
        'new_comment_to_unapproved_equipment_item',
        _('Your unapproved equipment item received a comment'),
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
        'new_image_comment_moderation',
        _('A new comment on your image requires moderation'),
        '',
        2,
    ),
    (
        'comment_approved',
        _('Your comment was approved'),
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
        'new_comment_like',
        _('Your comment was liked'),
        '',
        2,
    ),
    (
        'new_forum_post_like',
        _('Your forum post was liked'),
        '',
        2,
    ),
    (
        'forum_post_approved',
        _('Your forum post was approved'),
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
        'expiring_subscription_autorenew_30d',
        _('Your subscription will be renewed in one 30 days'),
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
    ),
    (
        'never_activated_account',
        _('Would you like to activate your account?'),
        '',
        2
    ),
    (
        'new_forum_reply',
        _('New reply in a subscribed forum topic'),
        '',
        2,
    ),
    (
        'new_forum_post_mention',
        _('You were mentioned in a forum post'),
        '',
        2,
    ),
    (
        'new_comment_mention',
        _('You were mentioned in a comment'),
        '',
        2,
    ),
    (
        'welcome_to_astrobin',
        _('Welcome to AstroBin!'),
        '',
        2,
    ),
    (
        'congratulations_for_your_first_image',
        _("Congratulations for your first image on AstroBin!"),
        '',
        2
    ),
    (
        'image_submitted_to_iotd_tp',
        _("Your image was submitted for IOTD/TP consideration"),
        '',
        2
    ),
    (
        'new_subscription',
        _("Thank you for getting a subscription!"),
        '',
        2
    ),
    (
        'new_payment',
        _("Thank you for your payment!"),
        '',
        2
    ),
    (
        'iotd_staff_inactive_removal_notice',
        _("You were removed from the IOTD staff"),
        '',
        2
    ),
    (
        'iotd_staff_inactive_warning',
        _("You have been inactive as an IOTD staff member"),
        '',
        2
    ),
    (
        'image_you_promoted_is_tp',
        _("An image you promoted made it to Top Pick"),
        '',
        2
    ),
    (
        'image_you_promoted_is_iotd',
        _("An image you promoted made it to IOTD"),
        '',
        2
    ),
    (
        'your_image_is_tpn',
        _("Your image was nominated to be a Top Pick"),
        '',
        2
    ),
    (
        'your_image_is_tp',
        _("Your image was voted Top Pick"),
        '',
        2
    ),
    (
        'your_image_is_iotd',
        _("Your image was voted Image of the Day"),
        '',
        2
    ),
    (
        'new_image_description_mention',
        _("You were mentioned in an image description"),
        '',
        2
    ),
    (
        'gear_renamed',
        _("A gear item that you used was renamed"),
        '',
        2
    ),
)
