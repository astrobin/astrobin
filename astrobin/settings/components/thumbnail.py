AVAILABLE_IMAGE_MODS = ('inverted',)

THUMBNAIL_DEBUG = DEBUG
THUMBNAIL_NAMER = 'easy_thumbnails.namers.source_hashed'
THUMBNAIL_ALWAYS_GENERATE = THUMBNAIL_DEBUG
THUMBNAIL_PROCESSORS = (
    # Keep before colorspace
    'astrobin.thumbnail_processors.tiff_force_8bit',
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
        'real': {
            'size': (16536, 0),
            'watermark': True,
            'keep_icc_profile': True,
        },
        'real_anonymized': {
            'size': (16536, 0),
            'watermark': False,
            'keep_icc_profile': True,
        },
        'real_inverted': {
            'size': (16536, 0),
            'invert': True,
            'watermark': True,
        },

        'hd': {
            'size': (1824, 0),
            'crop': 'smart',
            'watermark': True,
            'keep_icc_profile': True,
            'quality': 95,
        },
        'hd_anonymized': {
            'size': (1824, 0),
            'crop': 'smart',
            'watermark': False,
            'keep_icc_profile': True,
            'quality': 80,
        },
        'hd_inverted': {
            'size': (1824, 0),
            'crop': 'smart',
            'invert': True,
            'watermark': True,
            'quality': 80,
        },
        'hd_sharpened': {
            'size': (1824, 0),
            'crop': 'smart',
            'watermark': True,
            'detail': True,
            'keep_icc_profile': True,
            'quality': 80,
        },
        'hd_sharpened_inverted': {
            'size': (1824, 0),
            'crop': 'smart',
            'watermark': True,
            'detail': True,
            'invert': True,
            'quality': 80
        },

        'regular': {
            'size': (620, 0),
            'crop': 'smart',
            'watermark': True,
            'keep_icc_profile': True,
            'quality': 90
        },
        'regular_anonymized': {
            'size': (620, 0),
            'crop': 'smart',
            'watermark': False,
            'keep_icc_profile': True,
            'quality': 90
        },
        'regular_inverted': {
            'size': (620, 0),
            'crop': 'smart',
            'invert': True,
            'watermark': True,
            'quality': 90
        },
        'regular_sharpened': {
            'size': (620, 0),
            'crop': 'smart',
            'watermark': True,
            'detail': True,
            'keep_icc_profile': True,
            'quality': 90
        },
        'regular_sharpened_inverted': {
            'size': (620, 0),
            'crop': 'smart',
            'watermark': True,
            'detail': True,
            'invert': True,
            'quality': 90
        },

        'regular_large': {
            'size': (744, 0),
            'crop': 'smart',
            'watermark': True,
            'keep_icc_profile': True,
            'quality': 95
        },
        'regular_large_anonymized': {
            'size': (744, 0),
            'crop': 'smart',
            'watermark': False,
            'keep_icc_profile': True,
            'quality': 95
        },
        'regular_large_inverted': {
            'size': (744, 0),
            'crop': 'smart',
            'invert': True,
            'watermark': True,
            'quality': 95
        },
        'regular_large_sharpened': {
            'size': (744, 0),
            'crop': 'smart',
            'watermark': True,
            'detail': True,
            'keep_icc_profile': True,
            'quality': 95
        },
        'regular_large_sharpened_inverted': {
            'size': (744, 0),
            'crop': 'smart',
            'watermark': True,
            'detail': True,
            'invert': True,
            'quality': 95
        },

        'gallery': {
            'size': (130, 130),
            'crop': 'smart',
            'rounded': True,
            'quality': 75
        },
        'gallery_inverted': {
            'size': (130, 130),
            'crop': 'smart',
            'rounded': True,
            'quality': 75,
            'invert': True
        },
        'collection': {
            'size': (123, 123),
            'crop': 'smart',
            'quality': 60
        },
        'thumb': {
            'size': (80, 80),
            'crop': True,
            'rounded': 'smart',
            'quality': 60
        },

        # Tricks
        'histogram': {
            'size': (274, 120),
            'histogram': True
        },

        # IOTD
        'iotd': {
            'size': (1000, 380),
            'crop': 'smart',
            'watermark': True,
            'keep_icc_profile': True,
            'quality': 90
        },
        'iotd_mobile': {
            'size': (782, 480),
            'crop': 'smart',
            'watermark': True,
            'keep_icc_profile': True,
            'quality': 90
        },
        'iotd_candidate': {
            'size': (960, 0),
            'crop': 'smart',
            'watermark': False,
            'keep_icc_profile': True,
            'quality': 90
        },

        # Activity stream
        'story': {
            'size': (460, 320),
            'crop': 'smart',
            'quality': 90
        },
        'story_crop': {
            'size': (460, 320),
            'crop': 'smart',
            'zoom': 100,
            'upscale': True,
            'watermark': False,
            'keep_icc_profile': True,
            'quality': 90
        },

        # Duckduckgo
        'duckduckgo': {
            'size': (250, 200),
            'crop': 'smart',
            'quality': 80
        },
        'duckduckgo_small': {
            'size': (113, 90),
            'crop': 'smart',
            'quality': 80
        },

        # Social
        'instagram_story': {
            'size': (1080, 1920),
            'crop': 'smart',
            'quality': 80
        },
    },
}

THUMBNAIL_QUALITY = 100

if AWS_S3_ENABLED:
    THUMBNAIL_SUBDIR = '/thumbs'
else:
    THUMBNAIL_SUBDIR = 'thumbs'

THUMBNAIL_DEFAULT_STORAGE = DEFAULT_FILE_STORAGE

IMAGE_CROPPING_JQUERY_URL = None
IMAGE_CROPPING_SIZE_WARNING = True
IMAGE_CROPPING_THUMB_SIZE = (620, 0)
IMAGE_CROPPING_BACKEND = 'astrobin.widgets.hidden_image_crop_widget.EasyThumbnailsBackend'
