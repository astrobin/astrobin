from django.conf.urls import url, include
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from notification import urls as notification_urls

from astrobin_apps_notifications.views import TestNotificationView, NotificationListView, NotificationSettingsView

urlpatterns = (
    url(
        r'test-notification/(?P<username>[\w.@+-]+)/$',
        never_cache(login_required(TestNotificationView.as_view())),
        name='astrobin_apps_notifications.test_notification'),
    url(
        r'all/$',
        never_cache(login_required(NotificationListView.as_view())),
        name='astrobin_apps_notifications.all'),
    url(
        r'settings/$',
        never_cache(login_required(NotificationSettingsView.as_view())),
        name='astrobin_apps_notifications.settings'),
    url(r'_/', include(notification_urls)),
)
