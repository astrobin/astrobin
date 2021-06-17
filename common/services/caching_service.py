from datetime import datetime

from persistent_messages.models import Message
from rest_framework.authtoken.models import Token

from astrobin.models import UserProfile
from astrobin_apps_iotd.models import TopPickNominationsArchive, Iotd, TopPickArchive
from common.services import DateTimeService


class CachingService:
    @staticmethod
    def get_latest_top_pick_nomination_datetime(request):
        try:
            return TopPickNominationsArchive.objects.latest('image__published').image.published
        except TopPickNominationsArchive.DoesNotExist:
            return DateTimeService.now()

    @staticmethod
    def get_latest_top_pick_datetime(request):
        try:
            return TopPickArchive.objects.latest('image__published').image.published
        except TopPickArchive.DoesNotExist:
            return DateTimeService.now()

    @staticmethod
    def get_latest_iotd_datetime(request):
        try:
            return datetime.combine(Iotd.objects.latest('date').date, datetime.min.time())
        except Iotd.DoesNotExist:
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
            except Token.DoesNotExist:
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
    def get_last_notification_time(request):
        if request.user.is_authenticated():
            return Message.objects.filter(user=request.user).latest('modified').modified

        if 'HTTP_AUTHORIZATION' in request.META:
            token_in_header = request.META['HTTP_AUTHORIZATION'].replace('Token ', '')
            try:
                token = Token.objects.get(key=token_in_header)
                return Message.objects.filter(user=token.user).latest('modified').modified
            except Token.DoesNotExist:
                pass

        return DateTimeService.now()
