# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.dispatch import Signal

receiving = Signal(providing_args=['instance'])
received = Signal(providing_args=['instance'])
saving = Signal(providing_args=['instance'])
saved = Signal(providing_args=['instance'])
finished = Signal(providing_args=['instance'])
