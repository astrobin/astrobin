from django.conf.urls import url, include
from rest_framework import routers

from astrobin_apps_forum.api.views import PostViewSet
from astrobin_apps_forum.api.views import TopicViewSet
from astrobin_apps_forum.api.views import ForumViewSet
from astrobin_apps_forum.api.views import CategoryViewSet

router = routers.DefaultRouter()

router.register(r'post', PostViewSet, basename='post')
router.register(r'topic', TopicViewSet, basename='topic')
router.register(r'forum', ForumViewSet, basename='forum')
router.register(r'category', CategoryViewSet, basename='category')

urlpatterns = [
    url('', include(router.urls)),
]
