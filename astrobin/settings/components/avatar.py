import os

AVATAR_DEFAULT_URL = 'astrobin/images/default-avatar.jpeg?v=1'
AVATAR_STORAGE_DIR = 'images/avatars'
AVATAR_HASH_FILENAMES = True
AVATAR_HASH_USERDIRNAMES = True
AVATAR_RANDOMIZE_HASHES = True
AVATAR_EXPOSE_USERNAMES = False
AVATAR_DEFAULT_SIZE = 194
AVATAR_AUTO_GENERATE_SIZES = (64, 80, 194)
AVATAR_PROVIDERS = (
    'avatar.providers.PrimaryAvatarProvider',
    'avatar.providers.DefaultAvatarProvider',
)
AVATAR_MAX_SIZE = 1024 * 1024 * 15
AVATAR_CACHE_ENABLED = (
        os.environ.get('DEBUG', 'true').strip() != 'true' or
        os.environ.get('USE_CACHE_IN_DEBUG', 'true').strip() == 'true'
)
AVATAR_THUMB_FORMAT = 'png'
AVATAR_CLEANUP_DELETED = True
