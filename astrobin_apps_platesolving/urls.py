from django.conf.urls import url

from astrobin_apps_platesolving.views.solution import \
    SolutionFinalizeView, SolveAdvancedView, SolutionUpdateView, \
    SolveView, SolutionPixInsightWebhook, SolutionFinalizeAdvancedView, SolutionPixInsightNextTask

urlpatterns = (
    url(
        r'solve/(?P<object_id>\d+)/(?P<content_type_id>\d+)/$',
        SolveView.as_view(),
        name='astrobin_apps_platesolution.solve'),

    url(
        r'solve-advanced/(?P<object_id>\d+)/(?P<content_type_id>\d+)/$',
        SolveAdvancedView.as_view(),
        name='astrobin_apps_platesolution.solve_advanced'),

    url(
        r'update/(?P<pk>\d+)/$',
        SolutionUpdateView.as_view(),
        name='astrobin_apps_platesolution.update'),

    url(
        r'finalize/(?P<pk>\d+)/$',
        SolutionFinalizeView.as_view(),
        name='astrobin_apps_platesolution.finalize'),

    url(
        r'finalize-advanced/(?P<pk>\d+)/$',
        SolutionFinalizeAdvancedView.as_view(),
        name='astrobin_apps_platesolution.finalize'),

    url(
        r'pixinsight/next-task/$',
        SolutionPixInsightNextTask.as_view(),
        name='astrobin_apps_platesolution.pixinsight_next_task'),

    url(
        r'pixinsight/webhook/$',
        SolutionPixInsightWebhook.as_view(),
        name='astrobin_apps_platesolution.pixinsight_webhook'),
)
