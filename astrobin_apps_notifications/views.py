from django.http import HttpResponse
from django.views.generic.base import View, RedirectView

from astrobin.models import UserProfile
from astrobin_apps_notifications.utils import push_notification
from common.services import AppRedirectionService


class TestNotificationView(View):
    def post(request, *args, **kwargs):
        push_notification(
            [UserProfile.objects.get(user__username=kwargs.pop('username')).user],
            None,
            'test_notification',
            {})
        return HttpResponse("test_notification sent")


class NotificationListView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return AppRedirectionService.redirect(self.request, '/notifications')


class NotificationSettingsView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return AppRedirectionService.redirect(self.request, '/notifications/settings')
