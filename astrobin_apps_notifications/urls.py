# Django
from django.conf.urls import patterns, url, include
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

# Third party
from notification.views import notice_settings

# This app
from astrobin_apps_notifications.views import *


urlpatterns = patterns('',
    url(
        r'test-notification/(?P<username>[\w.@+-]+)/$',
        login_required(TestNotificationView.as_view()),
        name = 'astrobin_apps_notifications.test_notification'),
    url(
        r'all/$',
        login_required(NotificationListView.as_view()),
        name = 'astrobin_apps_notifications.all'),
    url(
        r'settings/$',
        login_required(notice_settings),
        name = 'astrobin_apps_notifications.settings'),
)
