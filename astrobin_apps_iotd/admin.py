from django.contrib import admin

from astrobin_apps_iotd.models import (
    IotdStaffMemberScore, IotdStats, IotdSubmission, IotdSubmissionQueueEntry, IotdVote, Iotd,
    TopPickNominationsArchive,
    TopPickArchive,
)


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


class IotdStatsAdmin(admin.ModelAdmin):
    pass


admin.site.register(IotdStats, IotdStatsAdmin)


class TopPickNominationsArchiveAdmin(admin.ModelAdmin):
    fields = ('image',)
    list_display = ('image',)


admin.site.register(TopPickNominationsArchive, TopPickNominationsArchiveAdmin)


class TopPickArchiveAdmin(admin.ModelAdmin):
    fields = ('image',)
    list_display = ('image',)


admin.site.register(TopPickArchive, TopPickArchiveAdmin)


class IotdSubmissionQueueEntryAdmin(admin.ModelAdmin):
    fields = ('image',)
    list_display = ('image',)


admin.site.register(IotdSubmissionQueueEntry, IotdSubmissionQueueEntryAdmin)


@admin.register(IotdStaffMemberScore)
class IotdStaffMemberScoreAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'created', 'period_start', 'period_end', 'score', 'active_days', 'promotions_dismissals_accuracy_ratio',
    )
    list_filter = ('created', 'period_start', 'period_end')
    search_fields = ('user__username', 'user__email')
    date_hierarchy = 'created'
    ordering = ('-score',)
    readonly_fields = (
        'user', 'created', 'period_start', 'period_end', 'score', 'active_days', 'promotions_dismissals_accuracy_ratio',
        'promotions', 'wasted_promotions', 'missed_iotd_promotions', 'missed_tp_promotions', 'missed_tpn_promotions',
        'promotions_to_tpn', 'promotions_to_tp', 'promotions_to_iotd', 'dismissals', 'correct_dismissals',
        'missed_dismissals', 'dismissals_to_tpn', 'dismissals_to_tp', 'dismissals_to_iotd',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
