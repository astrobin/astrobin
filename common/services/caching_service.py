from datetime import datetime

from django.conf import settings
from django.core.cache import cache
from persistent_messages.models import Message
from rest_framework.authtoken.models import Token

from astrobin.models import UserProfile, Image
from astrobin_apps_images.services import ImageService
from astrobin_apps_iotd.models import TopPickNominationsArchive, Iotd, TopPickArchive
from common.services import DateTimeService


class CachingService:
    @staticmethod
    def is_in_request_cache(key: str) -> bool:
        if settings.TESTING:
            return False

        from astrobin.middleware.thread_locals_middleware import get_request_cache
        request_cache = get_request_cache()
        return key in request_cache

    @staticmethod
    def get_from_request_cache(key: str) -> any:
        if settings.TESTING:
            return None

        from astrobin.middleware.thread_locals_middleware import get_request_cache
        request_cache = get_request_cache()
        return request_cache.get(key, None)

    @staticmethod
    def set_in_request_cache(key: str, value: any):
        if settings.TESTING:
            return

        from astrobin.middleware.thread_locals_middleware import get_request_cache
        request_cache = get_request_cache()
        request_cache[key] = value

    @staticmethod
    def delete_from_request_cache(key: str):
        if settings.TESTING:
            return

        from astrobin.middleware.thread_locals_middleware import get_request_cache
        request_cache = get_request_cache()
        if key in request_cache:
            del request_cache[key]

    @staticmethod
    def get(key, check_request_cache=True):
        if check_request_cache:
            is_present = CachingService.is_in_request_cache(key)
            value = CachingService.get_from_request_cache(key)
            if value is not None or is_present:
                return value

        value = cache.get(key)

        if check_request_cache and value is not None:
            CachingService.set_in_request_cache(key, value)

        return value

    @staticmethod
    def set(key, value, timeout=None, use_request_cache=True):
        if use_request_cache:
            CachingService.set_in_request_cache(key, value)
        cache.set(key, value, timeout)

    @staticmethod
    def delete(key, use_request_cache=True):
        if use_request_cache:
            CachingService.delete_from_request_cache(key)
        cache.delete(key)

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
            image = ImageService.get_object(id, Image.objects_including_wip_plain.only('updated'))
            return image.updated
        except (Image.DoesNotExist, AttributeError):
            return DateTimeService.now()

    @staticmethod
    def get_image_thumb_last_modified(request, id, r, alias):
        return CachingService.get_image_last_modified(request, id, r)
