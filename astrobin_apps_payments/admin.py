# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from astrobin_apps_payments.models import ExchangeRate


class ExchangeRateAdmin(admin.ModelAdmin):
    list_fields = ('source', 'target', 'rate', 'time')


admin.site.register(ExchangeRate, ExchangeRateAdmin)

