from django.conf.urls import url, include
from rest_framework import routers

from astrobin_apps_notifications.api.views import NotificationViewSet, NoticeSettingViewSet, NoticeTypeViewSet

router = routers.DefaultRouter()
router.register(r'notification', NotificationViewSet, base_name='notification')
router.register(r'type', NoticeTypeViewSet, base_name='type')
router.register(r'setting', NoticeSettingViewSet, base_name='setting')

urlpatterns = [
    url('', include(router.urls)),
]
