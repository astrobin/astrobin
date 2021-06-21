from datetime import datetime

from persistent_messages.models import Message
from rest_framework.authtoken.models import Token

from astrobin.models import UserProfile, Image
from astrobin_apps_images.services import ImageService
from astrobin_apps_iotd.models import TopPickNominationsArchive, Iotd, TopPickArchive
from common.services import DateTimeService


class CachingService:
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
        if request.user.is_authenticated():
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
            if request.user.is_authenticated():
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
