from django.contrib import admin

from astrobin_apps_iotd.models import IotdSubmission, IotdVote, Iotd, TopPickNominationsArchive, TopPickArchive


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
    list_display = ('pk', 'judge', 'image', 'date', 'created')
    list_filter = ('judge',)


admin.site.register(Iotd, IotdAdmin)


class TopPickNominationsArchiveAdmin(admin.ModelAdmin):
    fields = ('image',)
    list_display = ('image',)


admin.site.register(TopPickNominationsArchive, TopPickNominationsArchiveAdmin)


class TopPickArchiveAdmin(admin.ModelAdmin):
    fields = ('image',)
    list_display = ('image',)


admin.site.register(TopPickArchive, TopPickArchiveAdmin)
