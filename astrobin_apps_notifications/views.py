from braces.views import JSONResponseMixin
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.views.generic.base import View, RedirectView
from persistent_messages.models import Message

from astrobin.models import UserProfile
from astrobin_apps_notifications.utils import clear_notifications_template_cache, push_notification
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


class NotificationMarkAllAsReadView(View):
    def post(self, request, *args, **kwargs):
        Message.objects.filter(user=request.user).update(read=True)
        clear_notifications_template_cache(request.user.username)
        return redirect(request.POST.get('next', '/'))
