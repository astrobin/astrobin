# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

class ExchangeRate(models.Model):
    rate = models.DecimalField(max_digits=8, decimal_places=5)
    source = models.CharField(max_length=3)
    target = models.CharField(max_length=3)
    time = models.DateTimeField()

    def __unicode__(self):
        return "%s 1 = %s %f.5 on %s" % (
            self.source,
            self.target,
            float(self.rate),
            self.time
        )

    class Meta:
        app_label = 'astrobin_apps_payments'
