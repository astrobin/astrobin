from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.decorators.http import last_modified
from django.views.decorators.vary import vary_on_headers
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from notification.models import NOTICE_MEDIA, NoticeSetting, NoticeType
from persistent_messages.models import Message
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response

from astrobin.models import UserProfile
from astrobin_apps_notifications.api.filters import NotificationFilter
from astrobin_apps_notifications.api.serializers import (
    NoticeSettingSerializers, NoticeTypeSerializer,
    NotificationSerializer,
)
from common.permissions import ReadOnly
from common.services import DateTimeService
from common.services.caching_service import CachingService


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    filter_class = NotificationFilter
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    http_method_names = ['get', 'options', 'head', 'put']

    def get_queryset(self):
        return Message.objects.filter(user=self.request.user).order_by('-created')

    @method_decorator(
        last_modified(CachingService.get_last_notification_time),
        vary_on_headers('Cookie', 'Authorization')
    )
    @cache_control(must_revalidate=True)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    @vary_on_headers('Cookie', 'Authorization')
    @cache_control(must_revalidate=True)
    @method_decorator(last_modified(CachingService.get_last_notification_time))
    def get_unread_count(self, request):
        return Response(status=200, data=self.get_queryset().filter(read=False).count())

    @action(detail=False, methods=['put'])
    @cache_control(private=True, max_age=0, no_cache=True, no_store=True, must_revalidate=True)
    def mark_all_as_read(self, request):
        now = DateTimeService.now()
        self.get_queryset().filter(read=False).update(read=True, modified=now)
        UserProfile.objects.filter(user=request.user).update(last_notification_update=now)
        return Response(status=200)

    @action(detail=False, methods=['put'], url_path='mark-as-read-by-path-and-user')
    @cache_control(private=True, max_age=0, no_cache=True, no_store=True, must_revalidate=True)
    def mark_as_read_by_path_and_user(self, request):
        path: str = request.data.get('path')
        from_user_pk: int = request.data.get('fromUserPk')

        if path is None:
            return

        notifications = Message.objects.filter(user=request.user, message__contains=path, read=False)

        if from_user_pk is not None:
            notifications = notifications.filter(from_user__pk=from_user_pk)

        now = DateTimeService.now()
        notifications.update(read=True, modified=now)
        UserProfile.objects.filter(user=request.user).update(last_notification_update=now)

        return Response(status=200)

    @action(detail=True, methods=['put'], url_path='mark-as-read')
    @cache_control(private=True, max_age=0, no_cache=True, no_store=True, must_revalidate=True)
    def mark_as_read(self, request, pk):
        notification: Message = self.get_object()
        read: bool = request.data.get('read')
        notification.read = read
        notification.save()
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
                try:
                    # This will create it with default values if it doesn't exist.
                    NoticeSetting.for_user(self.request.user, notice_type, medium_id)
                except NoticeSetting.MultipleObjectsReturned:
                    NoticeSetting.objects.filter(
                        user=self.request.user, notice_type=notice_type, medium=medium_id
                    ).delete()
                    NoticeSetting.for_user(self.request.user, notice_type, medium_id)

        return NoticeSetting.objects.filter(user=self.request.user)
