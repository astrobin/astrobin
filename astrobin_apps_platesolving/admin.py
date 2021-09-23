# Django
from django.contrib import admin

from astrobin_apps_platesolving.models import Solution, PlateSolvingAdvancedTask


class SolutionAdmin(admin.ModelAdmin):
    list_display = (
        'object_id', 'content_type',
        'status', 'submission_id', 'image_file')
    list_filter = ('status',)


class AdvancedTaskAdmin(admin.ModelAdmin):
    list_display = ('serial_number', 'created', 'active',)
    list_filter = ('active',)


admin.site.register(Solution, SolutionAdmin)
admin.site.register(PlateSolvingAdvancedTask, AdvancedTaskAdmin)
