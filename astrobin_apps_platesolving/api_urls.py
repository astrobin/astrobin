from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from astrobin_apps_platesolving.views.solution import SolutionDetail
from astrobin_apps_platesolving.views.solution import SolutionList

urlpatterns = (
    url(r'^solutions/$', SolutionList.as_view(), name='api.astrobin_apps_platesolving.solution.list'),
    url(r'^solutions/(?P<pk>\d+)/$', SolutionDetail.as_view(), name='api.astrobin_apps_platesolving.solution.detail'),
)

# Format suffixes
urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json', 'api'])
