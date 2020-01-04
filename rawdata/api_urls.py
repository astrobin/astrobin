from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from .views.rawimage import *

urlpatterns = (
    url(r'^rawimages/$', RawImageList.as_view(), name='api.rawdata.rawimage.list'),
    url(r'^rawimages/(?P<pk>\d+)/$', RawImageDetail.as_view(), name='api.rawdata.rawimage.detail'),
)

# Format suffixes
urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json', 'api'])
