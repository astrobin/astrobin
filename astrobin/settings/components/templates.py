import os

local_path = lambda path: os.path.join(os.path.dirname(__file__), path)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            local_path('../templates'),
        ],
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',

                'pybb.context_processors.processor',

                'astrobin.context_processors.notices_count',
                'astrobin.context_processors.user_language',
                'astrobin.context_processors.user_profile',
                'astrobin.context_processors.user_scores',
                'astrobin.context_processors.common_variables',
            ],
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ],
            'debug': DEBUG,
        },
    },
]
