ASTROBIN_APPS = [
    'common',
    'nested_comments',
    'astrobin_apps_images',
    'astrobin_apps_platesolving',
    'astrobin_apps_users',
    'astrobin_apps_donations',
    'astrobin_apps_premium',
    'astrobin_apps_notifications',
    'astrobin_apps_groups',
    'astrobin_apps_iotd',
    'astrobin_apps_remote_source_affiliation',
    'astrobin_apps_equipment',
    'astrobin_apps_json_api',
    'astrobin_apps_payments',
    'toggleproperties',
    'astrobin_apps_forum',
]

INSTALLED_APPS = []

INSTALLED_APPS += ASTROBIN_APPS

INSTALLED_APPS += [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',

    'registration',
    'haystack',
    'notification',
    'persistent_messages',
    'gunicorn',
    'django_comments',
    'tagging',
    'tinymce',
    'hitcount',
    'avatar',
    'crispy_forms',
    'threaded_messages',
    'bootstrap_toolkit',
    'pipeline',
    'tastypie',
    'actstream',
    'paypal.standard.ipn',
    'subscription',
    'django_filters',
    'rest_framework',
    'rest_framework.authtoken',
    'easy_thumbnails',
    'el_pagination',
    'django_user_agents',
    'pybb',
    'precise_bbcode',
    'django_bootstrap_breadcrumbs',
    'silk',
    'djcelery_email',
    'django_celery_beat',
    'django_bouncy',
    'safedelete',
    'change_email',
    'template_timings_panel',
    'cookielaw',
    'corsheaders',
    'image_cropping',
    'django_extensions',
    'cachalot',
    'captcha',
    'django_celery_monitor',

    'astrobin.apps.AstroBinAppConfig',
]


if DEBUG:
    INSTALLED_APPS += [
        'debug_toolbar',
    ]
