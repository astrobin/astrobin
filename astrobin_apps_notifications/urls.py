from django.conf.urls import url, include
from django.contrib.auth.decorators import login_required
from notification import urls as notification_urls
from notification.views import notice_settings

from astrobin_apps_notifications.views import TestNotificationView, NotificationListView, NotificationMarkAllAsReadView, \
    NotificationClearTemplateCacheAjaxView

urlpatterns = (
    url(
        r'test-notification/(?P<username>[\w.@+-]+)/$',
        login_required(TestNotificationView.as_view()),
        name='astrobin_apps_notifications.test_notification'),
    url(
        r'all/$',
        login_required(NotificationListView.as_view()),
        name='astrobin_apps_notifications.all'),
    url(
        r'settings/$',
        login_required(notice_settings),
        name='astrobin_apps_notifications.settings'),
    url(
        r'mark-all-as-read/$',
        login_required(NotificationMarkAllAsReadView.as_view()),
        name='astrobin_apps_notifications.mark_all_as_read'),
    url(
        r'clear-template-cache/$',
        login_required(NotificationClearTemplateCacheAjaxView.as_view()),
        name='astrobin_apps_notifications.clear_template_cache'),
    url(r'_/', include(notification_urls)),
)
