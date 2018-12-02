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
        'You have a new follower',
        '',
        2,
    ),
    (
        'new_image',
        'New image from a user you follow',
        '',
        2,
    ),
    (
        'new_image_revision',
        'New image revision from a user you follow',
        '',
        2,
    ),
    (
        'image_solved',
        'Your image was plate-solved',
        '',
        1,
    ),
    (
        'image_not_solved',
        'Your image could not be plate-solved',
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
        'Your image received a new comment',
        '',
        2,
    ),
    (
        'new_comment_reply',
        'There was a reply to your comment',
        '',
        2,
    ),
    (
        'new_bookmark',
        'Your image was bookmarked',
        '',
        2,
    ),
    (
        'new_like',
        'Your image was liked',
        '',
        2,
    ),
    (
        'new_image_from_gear',
        'New image with some gear you follow',
        '',
        2,
    ),
    (
        'new_image_of_subject',
        'New image of a subject you follow',
        '',
        2,
    ),
    (
        'api_key_request_approved',
        'Your API Key request has been approved',
        '',
        2,
    ),
    (
        'new_gear_discussion',
        'New discussion about a gear item you own',
        '',
        2,
    ),
    (
        'new_gear_review',
        'New review of a gear item you own',
        '',
        2,
    ),
    (
        'rawdata_posted_to_pool',
        'New data posted to public pool',
        '',
        2,
    ),
    (
        'rawdata_posted_image_to_public_pool',
        'New image posted to public data pool',
        '',
        2,
    ),
    (
        'rawdata_posted_to_private_folder',
        'New data posted to shared private folder',
        '',
        2,
    ),
    (
        'rawdata_posted_image_to_private_folder',
        'New image posted to shared private folder',
        '',
        2,
    ),
    (
        'rawdata_invited_to_private_folder',
        'You are invited to a shared private folder',
        '',
        2,
    ),
    (
        'user_joined_public_group',
        'A user you follow joined a public group',
        '',
        2,
    ),
    (
        'new_group_invitation',
        'You are invited to a group',
        '',
        2,
    ),
    (
        'new_group_join_request',
        'A user requested to join a group you moderate',
        '',
        2,
    ),
    (
        'group_join_request_approved',
        'A group moderator approved your request to join',
        '',
        2,
    ),
    (
        'group_join_request_rejected',
        'A group moderator rejected your request to join',
        '',
        2,
    ),
    (
        'new_public_group_created',
        'A user you follow created a new public group',
        '',
        2,
    ),
    (
        'new_topic_in_group',
        'New forum topic in a group you are a member of',
        '',
        2,
    ),
    (
        'received_email',
        'You have received a new private message',
        '',
        2
    ),
    (
        'expiring_subscription',
        'Your premium subscription will expire in one week',
        '',
        2
    ),
    (
        'expiring_subscription_autorenew',
        'Your subscription will be renewed in one week',
        '',
        2
    )
)
