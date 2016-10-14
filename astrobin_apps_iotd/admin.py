from django.contrib import admin

# This app
from astrobin_apps_iotd.models import *


class IotdSubmissionAdmin(admin.ModelAdmin):
    fields = ('submitter', 'image', 'date')
    list_display = ('submitter', 'image', 'date')
    list_filter = ('date', 'submitter')
admin.site.register(IotdSubmission, IotdSubmissionAdmin)


class IotdVoteAdmin(admin.ModelAdmin):
    fields = ('reviewer', 'image', 'date')
    list_display = ('reviewer', 'image', 'date')
    list_filter = ('date', 'reviewer',)
admin.site.register(IotdVote, IotdVoteAdmin)


class IotdAdmin(admin.ModelAdmin):
    fields = ('judge', 'image', 'date', 'created')
    list_display = ('judge', 'image', 'date', 'created')
    list_filter = ('judge',)
admin.site.register(Iotd, IotdAdmin)
