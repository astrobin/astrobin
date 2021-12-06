from django.conf.urls import url, include
from rest_framework import routers

from astrobin_apps_forum.api.views.post_view_set import PostViewSet

router = routers.DefaultRouter()

router.register(r'post', PostViewSet, basename='post')

urlpatterns = [
    url('', include(router.urls)),
]
