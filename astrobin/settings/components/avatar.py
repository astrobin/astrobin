AVATAR_DEFAULT_URL = 'astrobin/images/astrobin-default-avatar.png?v=1'
AVATAR_STORAGE_DIR = 'images/avatars'
AVATAR_HASH_FILENAMES = True
AVATAR_HASH_USERDIRNAMES = True
AVATAR_RANDOMIZE_HASHES = True
AVATAR_EXPOSE_USERNAMES = False
AVATAR_AUTO_GENERATE_SIZES = (64, 80, 194)
AVATAR_PROVIDERS = (
    'avatar.providers.PrimaryAvatarProvider',
    'avatar.providers.DefaultAvatarProvider',
)
AVATAR_MAX_SIZE = 1024 * 1024 * 15
AVATAR_CACHE_ENABLED = not DEBUG
AVATAR_THUMB_FORMAT = 'png'
AVATAR_CLEANUP_DELETED = True
