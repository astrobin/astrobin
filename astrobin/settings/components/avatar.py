AVATAR_DEFAULT_URL = 'astrobin/images/astrobin-default-avatar.png?v=1'
AVATAR_STORAGE_DIR = 'images/avatars'
AVATAR_AUTO_GENERATE_SIZES = (64, 80, 194)
AVATAR_CACHE_ENABLED = not DEBUG
AVATAR_PROVIDERS = (
    'avatar.providers.PrimaryAvatarProvider',
    'avatar.providers.DefaultAvatarProvider',
)
AVATAR_MAX_SIZE = 1024 * 1024 * 15
AVATAR_CACHE_ENABLED = False
