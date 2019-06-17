# Django
from django.conf.urls import patterns, url
# Third party apps
from rest_framework.urlpatterns import format_suffix_patterns

# This app
from .views.rawimage import *

urlpatterns = patterns('',
                       url(r'^rawimages/$', RawImageList.as_view(), name='api.rawdata.rawimage.list'),
                       url(r'^rawimages/(?P<pk>\d+)/$', RawImageDetail.as_view(), name='api.rawdata.rawimage.detail'),
                       )

# Format suffixes
urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json', 'api'])
