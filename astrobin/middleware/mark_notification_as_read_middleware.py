import logging

from persistent_messages.models import Message

log = logging.getLogger("apps")


class MarkNotificationAsReadMiddleware(object):
    def _process(self, request):
        return (
                'nid' in request.GET and
                not request.is_ajax() and
                hasattr(request, 'user') and
                request.user.is_authenticated()
        )

    def process_request(self, request):
        if self._process(request):
            notification_id = request.GET.get('nid')

            try:
                notification = Message.objects.get(id=notification_id)
                if notification.user == request.user and not notification.read:
                    notification.read = True
                    notification.save()
            except Message.DoesNotExist:
                log.warning("Notification %s does not exist" % notification_id)
