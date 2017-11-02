from __future__ import absolute_import

# App initialization
default_app_config = 'astrobin.apps.AstroBinAppConfig'

# Custom monkeypatches
from .monkeypatch import *
