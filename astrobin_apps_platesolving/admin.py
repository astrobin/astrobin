# Django
from django.contrib import admin

from astrobin_apps_platesolving.models import Solution


class SolutionAdmin(admin.ModelAdmin):
    list_display = (
        'object_id', 'content_type',
        'status', 'submission_id', 'image_file')
    list_filter = ('status',)

admin.site.register(Solution, SolutionAdmin)

