from django.conf.urls import url, include
from rest_framework import routers

from astrobin_apps_groups.api.views.group_view_set import GroupViewSet

router = routers.DefaultRouter()
router.register(r'group', GroupViewSet, base_name='group')

urlpatterns = [
    url('', include(router.urls)),
]
