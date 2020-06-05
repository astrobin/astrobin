from django.contrib import admin

from astrobin_apps_remote_source_affiliation.models import RemoteSourceAffiliate


class RemoteSourceAffiliateAdmin(admin.ModelAdmin):
    fields = (
        'code',
        'name',
        'url',
        'affiliation_start',
        'affiliation_expiration',
        'image_file',
    )

    list_display = (
        'code',
        'name',
        'url',
        'affiliation_start',
        'affiliation_expiration',
    )

    list_editable = (
        'name',
        'url',
        'affiliation_start',
        'affiliation_expiration',
    )


admin.site.register(RemoteSourceAffiliate, RemoteSourceAffiliateAdmin)
