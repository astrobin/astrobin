# Django
from django.conf.urls.defaults import *
from django.contrib.auth.decorators import login_required

# Third party apps
from rest_framework.urlpatterns import format_suffix_patterns

# This app
from .views import *


urlpatterns = patterns('',
    url(r'^contenttypes/$', ContentTypeList.as_view(), name='contenttype-list'),
    url(r'^contenttypes/(?P<pk>\d+)/$', ContentTypeDetail.as_view(), name='contenttype-detail'),


    url(r'^users/$', UserList.as_view(), name='user-list'),
    url(r'^users/(?P<pk>\d+)/$', UserDetail.as_view(), name='user-detail'),

    url(r'^nestedcomments/$', NestedCommentList.as_view(), name='nestedcomment-list'),
    url(r'^nestedcomments/(?P<pk>\d+)/$', NestedCommentDetail.as_view(), name='nestedcomment-detail'),
)

# Format suffixes
urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json', 'api'])

