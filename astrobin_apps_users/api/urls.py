from django.conf.urls import url, include
from rest_framework import routers

from astrobin_apps_users.api.views.user_fancybox_list_view_set import UserFancyboxListViewSet
from astrobin_apps_users.api.views.user_locations_view_set import UserLocationsViewSet

router = routers.DefaultRouter()
router.register(r'locations', UserLocationsViewSet, basename='locations')
router.register(r'fancybox-list', UserFancyboxListViewSet, basename='fancybox-list')

urlpatterns = [
    url('', include(router.urls)),
]
