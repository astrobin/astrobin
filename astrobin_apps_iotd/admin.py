from django.contrib import admin

from astrobin_apps_iotd.models import IotdSubmission, IotdVote, Iotd


class IotdSubmissionAdmin(admin.ModelAdmin):
    fields = ('submitter', 'image')
    readonly_fields = ('date',)
    list_display = ('submitter', 'image')
    list_filter = ('submitter',)
admin.site.register(IotdSubmission, IotdSubmissionAdmin)


class IotdVoteAdmin(admin.ModelAdmin):
    fields = ('reviewer', 'image')
    readonly_fields = ('date',)
    list_display = ('reviewer', 'image')
    list_filter = ('reviewer',)
admin.site.register(IotdVote, IotdVoteAdmin)


class IotdAdmin(admin.ModelAdmin):
    fields = ('judge', 'image', 'date')
    list_display = ('pk', 'judge', 'image', 'created')
    list_filter = ('judge',)
admin.site.register(Iotd, IotdAdmin)
