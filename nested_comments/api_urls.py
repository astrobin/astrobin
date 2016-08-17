# Django
from django.conf.urls import patterns, url, include

# Third party apps
from rest_framework.urlpatterns import format_suffix_patterns

# This app
from .views import *


urlpatterns = patterns('',
    url(r'^nestedcomments/$', NestedCommentList.as_view(), name='nestedcomment-list'),
    url(r'^nestedcomments/(?P<pk>\d+)/$', NestedCommentDetail.as_view(), name='nestedcomment-detail'),
)

# Format suffixes
urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json', 'api'])

