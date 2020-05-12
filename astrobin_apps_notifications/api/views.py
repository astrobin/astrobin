from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from persistent_messages.models import Message
from rest_framework import viewsets, permissions
from rest_framework.decorators import list_route
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response

from astrobin_apps_notifications.api.serializers import NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]

    def get_queryset(self):
        return Message.objects.filter(user=self.request.user).order_by('-created')

    @list_route(methods=['get'])
    def get_unread_count(self, request):
        return Response(status=200, data=self.get_queryset().filter(read=False).count())

    @list_route(methods=['post'])
    def mark_all_as_read(self, request):
        self.get_queryset().update(read=True)
        return Response(status=200)
