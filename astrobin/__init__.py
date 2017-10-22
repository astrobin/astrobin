from __future__ import absolute_import

# Celery
from .celery import app as celery_app

# App initialization
default_app_config = 'astrobin.apps.AstroBinAppConfig'

# Custom monkeypatches
from .monkeypatch import *
