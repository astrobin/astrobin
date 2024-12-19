from django.conf.urls import url
from django.urls import include
from rest_framework.routers import SimpleRouter
from rest_framework.urlpatterns import format_suffix_patterns

from astrobin_apps_platesolving.views.settings import PlateSolvingAdvancedSettingsViewSet, PlateSolvingSettingsViewSet
from astrobin_apps_platesolving.views.solution import (
    SolutionDetail, AdvancedTaskList, SolutionPixInsightMatrix,
    SolutionRestartView,
)
from astrobin_apps_platesolving.views.solution import SolutionList

router = SimpleRouter()
router.register(r'settings', PlateSolvingSettingsViewSet, basename='settings')
router.register(r'advanced-settings', PlateSolvingAdvancedSettingsViewSet, basename='advanced-settings')

# TODO: migrate to ViewSets.
urlpatterns = [
    url(r'^solutions/$', SolutionList.as_view(), name='api.astrobin_apps_platesolving.solution.list'),
    url(r'^solutions/(?P<pk>\d+)/$', SolutionDetail.as_view(), name='api.astrobin_apps_platesolving.solution.detail'),
    url(r'^solutions/(?P<pk>\d+)/restart/$', SolutionRestartView.as_view(), name='api.astrobin_apps_platesolving.solution.restart'),
    url(r'^solutions/(?P<pk>\d+)/advanced-matrix/$', SolutionPixInsightMatrix.as_view(), name='api.astrobin_apps_platesolving.solution.advanced_matrix'),
    url(r'^advanced-task/$', AdvancedTaskList.as_view(), name='api.astrobin_apps_platesolving.advanced-task.list'),
    url('', include(router.urls)),
]

# Apply format suffixes to all URLs (since SimpleRouter doesn't handle formats by default)
urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json', 'api'])
