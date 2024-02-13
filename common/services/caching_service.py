from datetime import datetime

from django.core.cache import caches
from persistent_messages.models import Message
from rest_framework.authtoken.models import Token

from astrobin.models import UserProfile, Image
from astrobin_apps_images.services import ImageService
from astrobin_apps_iotd.models import TopPickNominationsArchive, Iotd, TopPickArchive
from common.services import DateTimeService


class CachingService:
    @staticmethod
    def get_local(key):
        local_cache = caches['local_request_cache']
        return local_cache.get(key)

    @staticmethod
    def set_local(key, value, timeout=None):
        local_cache = caches['local_request_cache']
        local_cache.set(key, value, timeout)

    @staticmethod
    def get(key, prefer_local_cache=True):
        if prefer_local_cache:
            value = CachingService.get_local(key)
            if value is not None:
                return value

        value = caches['default'].get(key)
        if prefer_local_cache and value is not None:
            CachingService.set_local(key, value)

        return value

    @staticmethod
    def set(key, value, timeout=None, prefer_local_cache=True):
        caches['default'].set(key, value, timeout)
        if prefer_local_cache:
            CachingService.set_local(key, value, timeout)

    @staticmethod
    def get_latest_top_pick_nomination_datetime(request):
        try:
            return TopPickNominationsArchive.objects.latest('image__published').image.published
        except (TopPickNominationsArchive.DoesNotExist, AttributeError):
            return DateTimeService.now()

    @staticmethod
    def get_latest_top_pick_datetime(request):
        try:
            return TopPickArchive.objects.latest('image__published').image.published
        except (TopPickArchive.DoesNotExist, AttributeError):
            return DateTimeService.now()

    @staticmethod
    def get_latest_iotd_datetime(request):
        try:
            return datetime.combine(Iotd.objects.latest('date').date, datetime.min.time())
        except (Iotd.DoesNotExist, AttributeError):
            return DateTimeService.now()

    @staticmethod
    def get_current_user_profile_last_modified(request):
        if request.user.is_authenticated:
            return request.user.userprofile.updated

        if 'HTTP_AUTHORIZATION' in request.META:
            token_in_header = request.META['HTTP_AUTHORIZATION'].replace('Token ', '')
            try:
                token = Token.objects.get(key=token_in_header)
                return token.user.userprofile.updated
            except (Token.DoesNotExist, AttributeError):
                pass

        return DateTimeService.now()

    @staticmethod
    def get_user_detail_last_modified(request, pk):
        try:
            userprofile = UserProfile.objects.get(user__pk=pk)
            return userprofile.updated
        except UserProfile.DoesNotExist:
            return DateTimeService.now()

    @staticmethod
    def get_userprofile_detail_last_modified(request, pk):
        try:
            userprofile = UserProfile.objects.get(pk=pk)
            return userprofile.updated
        except UserProfile.DoesNotExist:
            return DateTimeService.now()

    @staticmethod
    def get_user_page_last_modified(request, username):
        try:
            userprofile = UserProfile.objects.get(user__username=username)
            return userprofile.updated
        except (UserProfile.DoesNotExist, AttributeError):
            return DateTimeService.now()

    @staticmethod
    def get_last_notification_time(request, pk=None):
        if pk:
            try:
                return Message.objects.get(pk=pk).modified
            except (Message.DoesNotExist, AttributeError):
                pass
        else:
            if request.user.is_authenticated:
                try:
                    return Message.objects.filter(user=request.user).latest('modified').modified
                except (Message.DoesNotExist, AttributeError):
                    pass

            if 'HTTP_AUTHORIZATION' in request.META:
                token_in_header = request.META['HTTP_AUTHORIZATION'].replace('Token ', '')
                try:
                    token = Token.objects.get(key=token_in_header)
                    return Message.objects.filter(user=token.user).latest('modified').modified
                except (Token.DoesNotExist, Message.DoesNotExist, AttributeError):
                    pass

        return DateTimeService.now()

    @staticmethod
    def get_image_last_modified(request, id, r):
        try:
            image = ImageService.get_object(id, Image.objects_including_wip)
            return image.updated
        except (Image.DoesNotExist, AttributeError):
            return DateTimeService.now()

    @staticmethod
    def get_image_thumb_last_modified(request, id, r, alias):
        return CachingService.get_image_last_modified(request, id, r)
