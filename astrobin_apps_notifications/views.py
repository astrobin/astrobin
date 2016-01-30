# Django
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.views.generic.base import View
from django.views.generic.list import ListView

# Third party
from persistent_messages.models import Message

# This app
from astrobin_apps_notifications.utils import push_notification

class TestNotificationView(View):
    def post(request, *args, **kwargs):
        push_notification(
            [User.objects.get(username = kwargs.pop('username'))],
            'test_notification',
            {})
        return HttpResponse("test_notification sent")


class NotificationListView(ListView):
    model = Message
    template_name = "astrobin_apps_notifications/all.html"
    context_object_name = "notification_list"

    def get_queryset(self):
        return Message.objects\
            .filter(user = self.request.user)\
            .order_by('read', '-created')
