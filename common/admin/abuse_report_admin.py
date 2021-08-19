from django.contrib import admin


class AbuseReportAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'content_owner',
        'reason',
        'decision'
    )
