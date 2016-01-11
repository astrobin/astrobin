# Django
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.views.generic.base import View

# This app
from astrobin_apps_notifications.utils import push_notification

class TestNotificationView(View):
    def post(request, *args, **kwargs):
        push_notification(
            [User.objects.get(username = kwargs.pop('username'))],
            'test_notification',
            {})
        return HttpResponse("test_notification sent")
