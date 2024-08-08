from django.conf.urls import url
from django.urls import include
from rest_framework import routers

from nested_comments.views import NestedCommentSearchViewSet, NestedCommentViewSet

router = routers.DefaultRouter()
router.register(r'nestedcomments', NestedCommentViewSet, basename='nestedcomments')
router.register(r'nestedcomments-search', NestedCommentSearchViewSet, basename='nestedcomments-search')

urlpatterns = [
    url('', include(router.urls)),
]
