from django.conf.urls import url, include
from rest_framework import routers

from astrobin_apps_notifications.api.views import NotificationViewSet

router = routers.DefaultRouter()
router.register(r'notification', NotificationViewSet, base_name='notification')

urlpatterns = [
    url('', include(router.urls)),
]
