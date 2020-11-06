AVAILABLE_IMAGE_MODS = ('inverted',)

THUMBNAIL_DEBUG = DEBUG
THUMBNAIL_NAMER = 'easy_thumbnails.namers.source_hashed'
THUMBNAIL_ALWAYS_GENERATE = THUMBNAIL_DEBUG
THUMBNAIL_PROCESSORS = (
    # Keep before colorspace
    'astrobin.thumbnail_processors.srgb_processor',

    'image_cropping.thumbnail_processors.crop_corners',

    # Default processors
    'easy_thumbnails.processors.colorspace',
    'easy_thumbnails.processors.autocrop',
    'easy_thumbnails.processors.scale_and_crop',
    'easy_thumbnails.processors.filters',

    # AstroBin processors
    'astrobin.thumbnail_processors.rounded_corners',
    'astrobin.thumbnail_processors.invert',
    'astrobin.thumbnail_processors.watermark',
    'astrobin.thumbnail_processors.histogram',
)

THUMBNAIL_ALIASES = {
    '': {
        # Main image thumbnails
        'real': {'size': (16536, 16536), 'watermark': True, 'keep_icc_profile': True},
        'real_inverted': {'size': (16536, 16536), 'invert': True, 'watermark': True},

        'hd': {'size': (1824, 0), 'crop': 'smart', 'watermark': True, 'keep_icc_profile': True},
        'hd_anonymized': {'size': (1824, 0), 'crop': 'smart', 'watermark': False, 'keep_icc_profile': True},
        'hd_inverted': {'size': (1824, 0), 'crop': 'smart', 'invert': True, 'watermark': True},
        'hd_sharpened': {'size': (1824, 0), 'crop': 'smart', 'watermark': True, 'detail': True, 'keep_icc_profile': True},
        'hd_sharpened_inverted': {'size': (1824, 0), 'crop': 'smart', 'watermark': True, 'detail': True, 'invert': True},

        'regular': {'size': (620, 0), 'crop': 'smart', 'watermark': True, 'keep_icc_profile': True},
        'regular_inverted': {'size': (620, 0), 'crop': 'smart', 'invert': True, 'watermark': True},
        'regular_sharpened': {'size': (620, 0), 'crop': 'smart', 'watermark': True, 'detail': True,
                              'keep_icc_profile': True},
        'regular_sharpened_inverted': {'size': (620, 0), 'crop': 'smart', 'watermark': True, 'detail': True, 'invert': True},

        'gallery': {'size': (130, 130), 'crop': 'smart', 'rounded': True, 'quality': 80},
        'gallery_inverted': {'size': (130, 130), 'crop': 'smart', 'rounded': True, 'quality': 80, 'invert': True},
        'collection': {'size': (123, 123), 'crop': 'smart', 'quality': 60},
        'thumb': {'size': (80, 80), 'crop': True, 'rounded': 'smart', 'quality': 60},

        # Tricks
        'histogram': {'size': (274, 120), 'histogram': True},

        # IOTD
        'iotd': {'size': (1000, 380), 'crop': 'smart', 'watermark': True, 'keep_icc_profile': True},
        'iotd_mobile': {'size': (782, 480), 'crop': 'smart', 'watermark': True, 'keep_icc_profile': True},
        'iotd_candidate': {'size': (960, 0), 'crop': 'smart', 'watermark': False, 'keep_icc_profile': True},

        # Activity stream
        'story': {'size': (460, 320), 'crop': 'smart', 'quality': 90},

        # Duckduckgo
        'duckduckgo': {'size': (250, 200), 'crop': 'smart', 'quality': 80},
        'duckduckgo_small': {'size': (113, 90), 'crop': 'smart', 'quality': 80},

        # Social
        'instagram_story': {'size': (1080, 1920), 'crop': 'smart', 'quality': 80},
    },
}
THUMBNAIL_QUALITY = 100
THUMBNAIL_SUBDIR = 'thumbs'
THUMBNAIL_DEFAULT_STORAGE = DEFAULT_FILE_STORAGE

IMAGE_CROPPING_JQUERY_URL = None
IMAGE_CROPPING_SIZE_WARNING = True
IMAGE_CROPPING_THUMB_SIZE = (620, 620)
