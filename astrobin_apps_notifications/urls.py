# Django
from django.conf.urls.defaults import *
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

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
)
