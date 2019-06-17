from __future__ import absolute_import

# App initialization
default_app_config = 'astrobin.apps.AstroBinAppConfig'

from .celery import app as celery_app

# Custom monkeypatches

__all__ = ['celery_app']
