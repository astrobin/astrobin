from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.decorators.http import last_modified
from django.views.decorators.vary import vary_on_cookie
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from notification.models import NoticeSetting, NoticeType, NOTICE_MEDIA
from persistent_messages.models import Message
from rest_framework import viewsets, permissions
from rest_framework.decorators import list_route
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response

from astrobin_apps_notifications.api.filters import NotificationFilter
from astrobin_apps_notifications.api.serializers import NotificationSerializer, NoticeSettingSerializers, \
    NoticeTypeSerializer
from common.permissions import ReadOnly
from common.services.caching_service import CachingService


@method_decorator([
    last_modified(CachingService.get_last_notification_time),
    cache_control(private=True, no_cache=True),
    vary_on_cookie
], name='dispatch')
class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    filter_class = NotificationFilter
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    http_method_names = ['get', 'post', 'head', 'put']

    def get_queryset(self):
        return Message.objects.filter(user=self.request.user).order_by('-created')

    @list_route(methods=['get'])
    def get_unread_count(self, request):
        return Response(status=200, data=self.get_queryset().filter(read=False).count())

    @list_route(methods=['post'])
    def mark_all_as_read(self, request):
        self.get_queryset().update(read=True)
        return Response(status=200)


class NoticeTypeViewSet(viewsets.ModelViewSet):
    serializer_class = NoticeTypeSerializer
    permission_classes = [ReadOnly]
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    queryset = NoticeType.objects.all()
    pagination_class = None


class NoticeSettingViewSet(viewsets.ModelViewSet):
    serializer_class = NoticeSettingSerializers
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    pagination_class = None

    def get_queryset(self):
        notice_types = NoticeType.objects.all()
        for notice_type in notice_types:
            for medium_id, medium_display in NOTICE_MEDIA:
                # This will create it with default values if it doesn't exist.
                NoticeSetting.for_user(self.request.user, notice_type, medium_id)

        return NoticeSetting.objects.filter(user=self.request.user)
