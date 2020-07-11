# -*- coding: utf-8 -*-
from __future__ import unicode_literals

try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse

try:
    from base64 import b64encode as encode_base64
except (ImportError, AttributeError):
    from base64 import encodestring as encode_base64

try:
    from base64 import b64decode as decode_base64
except (ImportError, AttributeError):
    from base64 import decodestring as decode_base64
