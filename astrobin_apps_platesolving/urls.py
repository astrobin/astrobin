from django.conf.urls import url

from astrobin_apps_platesolving.views import ServeAdvancedSvg
from astrobin_apps_platesolving.views.solution import (
    SolutionPixInsightWebhook, SolutionPixInsightNextTask, SolutionPixInsightLiveLogWebhook,
)

urlpatterns = (
    url(
        r'pixinsight/next-task/$',
        SolutionPixInsightNextTask.as_view(priority='normal'),
        name='astrobin_apps_platesolving.pixinsight_next_task'
    ),
    
    url(
        r'pixinsight/next-task-low-priority/$',
        SolutionPixInsightNextTask.as_view(priority='low'),
        name='astrobin_apps_platesolving.pixinsight_next_task_low_priority'
    ),

    url(
        r'pixinsight/webhook/$',
        SolutionPixInsightWebhook.as_view(),
        name='astrobin_apps_platesolving.pixinsight_webhook'
    ),

    url(
        r'pixinsight/live-log-webhook/$',
        SolutionPixInsightLiveLogWebhook.as_view(),
        name='astrobin_apps_platesolving.pixinsight_live_log_webhook'
    ),

    url(
        r'solution/(?P<pk>\d+)/svg/(?P<resolution>\w+)/$',
        ServeAdvancedSvg.as_view(),
        name='astrobin_apps_platesolving.serve_svg'
    )
)
