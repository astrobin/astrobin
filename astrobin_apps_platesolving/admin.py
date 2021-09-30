from django.contrib import admin

from astrobin_apps_platesolving.models import Solution, PlateSolvingAdvancedTask, PlateSolvingAdvancedLiveLogEntry


class SolutionAdmin(admin.ModelAdmin):
    list_display = (
        'object_id', 'content_type',
        'status', 'submission_id', 'image_file')
    list_filter = ('status',)


class AdvancedTaskAdmin(admin.ModelAdmin):
    list_display = ('serial_number', 'created', 'active',)
    list_filter = ('active',)


class AdvancedLiveLogEntryAdmin(admin.ModelAdmin):
    list_display = ('serial_number', 'timestamp', 'stage')
    search_fields = ('serial_number',)


admin.site.register(Solution, SolutionAdmin)
admin.site.register(PlateSolvingAdvancedTask, AdvancedTaskAdmin)
admin.site.register(PlateSolvingAdvancedLiveLogEntry, AdvancedLiveLogEntryAdmin)
