from django.contrib import admin


class AbuseReportAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'reason',
        'decision'
    )
