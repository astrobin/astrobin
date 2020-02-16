from __future__ import absolute_import

# App initialization
default_app_config = 'astrobin.apps.AstroBinAppConfig'

from .celery import app as celery_app

# Custom monkeypatches
from .monkeypatch import _get_image_dimensions

__all__ = ['celery_app']
