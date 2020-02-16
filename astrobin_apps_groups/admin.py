from django.contrib import admin

from astrobin_apps_groups.models import Group


class GroupAdmin(admin.ModelAdmin):
    fields = (
        'name',
        'description',
        'category',
        'public',
        'moderated',
        'autosubmission',
    )
    list_display = (
        'pk',
        'name',
        'date_created',
        'creator',
        'owner',
    )
    list_editable = ('name',)
    list_filter = ('public', 'moderated', 'autosubmission',)
    search_fields = ('owner', 'creator', 'name', 'description',)
    ordering = ('-date_created',)


admin.site.register(Group, GroupAdmin)
