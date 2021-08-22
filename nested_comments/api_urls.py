from django.conf.urls import url
from django.urls import include
from rest_framework import routers

from nested_comments.views import NestedCommentViewSet

router = routers.DefaultRouter()
router.register(r'nestedcomments', NestedCommentViewSet, basename='nestedcomments')

urlpatterns = [
    url('', include(router.urls)),
]
