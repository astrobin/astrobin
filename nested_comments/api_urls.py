from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from nested_comments.views import NestedCommentList, NestedCommentDetail

urlpatterns = (
    url(r'^nestedcomments/$', NestedCommentList.as_view(), name='nestedcomment-list'),
    url(r'^nestedcomments/(?P<pk>\d+)/$', NestedCommentDetail.as_view(), name='nestedcomment-detail'),
)

# Format suffixes
urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json', 'api'])
