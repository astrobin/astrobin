from django.contrib import admin

from common.admin.abuse_report_admin import AbuseReportAdmin
from common.models import AbuseReport

admin.site.register(AbuseReport, AbuseReportAdmin)

