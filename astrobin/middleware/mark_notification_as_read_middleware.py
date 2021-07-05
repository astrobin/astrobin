import logging

from django.utils import timezone
from persistent_messages.models import Message

log = logging.getLogger("apps")


class MarkNotificationAsReadMiddleware(object):
    def _process_with_nid(self, request):
        return (
                'nid' in request.GET and
                not request.is_ajax() and
                hasattr(request, 'user') and
                request.user.is_authenticated()
        )

    def _process_with_email_medium(self, request):
        return (
                'utm_source' in request.GET and
                'utm_medium' in request.GET and
                'utm_campaign' in request.GET and
                request.GET.get('utm_source') == 'astrobin' and
                request.GET.get('utm_medium') == 'email' and
                request.GET.get('utm_campaign') == 'notification' and
                not request.is_ajax() and
                hasattr(request, 'user') and
                request.user.is_authenticated()
        )

    def process_request(self, request):
        if self._process_with_nid(request):
            notification_id = request.GET.get('nid')

            try:
                notification = Message.objects.get(id=notification_id)
                if notification.user == request.user and not notification.read:
                    notification.read = True
                    notification.save()
            except Message.DoesNotExist:
                log.warning("Notification %s does not exist" % notification_id)
        elif self._process_with_email_medium(request):
            notifications = Message.objects.filter(user=request.user, message__contains=request.path, read=False)

            if 'from_user' in request.GET:
                try:
                    from_user_pk = int(request.GET.get('from_user'))
                    notifications = notifications.filter(from_user__pk=from_user_pk)
                except ValueError:
                    pass

            notifications.update(read=True, modified=timezone.now())
