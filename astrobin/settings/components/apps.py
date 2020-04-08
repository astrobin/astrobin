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
    'toggleproperties'
]

INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',

    # Third party apps
    'registration',
    'haystack',
    'notification',
    'persistent_messages',
    'celery_haystack',
    'gunicorn',
    'django_comments',
    'tagging',
    'mptt',
    'tinymce',
    'hitcount',
    'avatar',
    'crispy_forms',
    'threaded_messages',
    'bootstrap_toolkit',
    'contact_form',
    'pipeline',
    'tastypie',
    'reviews',
    'actstream',
    'modeltranslation',
    'paypal.standard.ipn',
    'subscription',
    'ember',
    'django_filters',
    'rest_framework',
    'rest_framework.authtoken',
    'easy_thumbnails',
    'el_pagination',
    'dfp',  # For Google DFP
    'django_user_agents',
    'pybb',  # Forum
    'markup_deprecated',
    'sanitizer',
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
    'progressbarupload',

    'astrobin.apps.AstroBinAppConfig',
] + ASTROBIN_APPS

if DEBUG:
     INSTALLED_APPS += [
          'debug_toolbar',
     ]
