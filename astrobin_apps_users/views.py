import ipaddress
import json
import logging

from braces.views import JSONResponseMixin, LoginRequiredMixin, JsonRequestResponseMixin
from django.conf import settings
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse
from django.db.models import Q
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.utils.translation import gettext
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import base
from django_bouncy.models import Bounce, Complaint

from astrobin.models import UserProfile
from astrobin.utils import get_client_ip
from toggleproperties.models import ToggleProperty

logger = logging.getLogger(__name__)

class TogglePropertyUsersAjaxView(JsonRequestResponseMixin, base.View):
    def get(self, request, *args, **kwargs):
        property_type = kwargs.pop('property_type')
        object_id = kwargs.pop('object_id')
        content_type = ContentType.objects.get_for_id(kwargs.pop('content_type_id'))

        toggle_properties = ToggleProperty.objects.filter(
            property_type=property_type,
            object_id=object_id,
            content_type=content_type,
            user__isnull=False,
        )

        data = []
        for toggle_property in toggle_properties.iterator():
            data.append({
                'id': toggle_property.id,
                'userId': toggle_property.user.id,
                'username': toggle_property.user.username,
                'displayName': toggle_property.user.userprofile.get_display_name(),
                'createdOn': toggle_property.created_on,
                'following': ToggleProperty.objects.toggleproperties_for_object(
                    'follow', toggle_property.user, request.user).exists() if request.user.is_authenticated else False
            })

        return self.render_json_response(json.dumps(data, cls=DjangoJSONEncoder))


class UserSearchView(JSONResponseMixin, base.View):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        term = request.GET.get('term')

        profiles = UserProfile.objects.filter(
            Q(user__first_name__icontains=term) |
            Q(user__last_name__icontains=term) |
            Q(user__username__icontains=term) |
            Q(real_name__icontains=term))

        if request.is_ajax():
            matches = []
            for profile in profiles:
                matches.append({
                    'id': profile.user.pk,
                    'username': profile.user.username,
                    'display_name': profile.get_display_name(),
                    'url': reverse('user_page', args=(profile.user.username,)),
                })

            return self.render_json_response(matches)


class BounceIgnoreAndRetryView(LoginRequiredMixin, View):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        Bounce.objects.filter(address=request.user.email).delete()
        messages.success(request, gettext(
            "Your email bounce reports have been removed from AstroBin. Please make sure that your email works well or "
            "you will get the same warning message again. Thanks!"))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


class ComplaintRemove(LoginRequiredMixin, View):
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        Complaint.objects.filter(address=request.user.email).delete()
        messages.success(request, gettext(
            "Your spam reports have been removed from AstroBin. Please make sure you don't have a filter or rule to "
            "always mark AstroBin's emails as spam! If you don't want to receive emails from AstroBin, look for the "
            "settings link that's at the bottom of every email. Thanks!"))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@method_decorator(csrf_exempt, name='dispatch')
class BrevoWebhook(View):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs) -> HttpResponse:
        data_str = request.body.decode('utf-8')

        logger.debug('Brevo webhook data: %s', data_str)

        data = json.loads(data_str)

        client_ip = get_client_ip(request)
        if not self.is_valid_ip(client_ip):
            logger.error('Request from invalid IP: %s', client_ip)
            return HttpResponseForbidden()

        event: str = self.get_event(data)
        if event is None:
            logger.error('Missing event in Brevo webhook')
            return HttpResponse(status=400)

        email: str = self.get_email(data)
        if email is None:
            logger.error('Missing email in Brevo webhook')
            return HttpResponse(status=400)

        user_profile: UserProfile = self.get_user_profile(email)
        if user_profile is None:
            logger.error('User %s not found in Brevo webhook', email)
            return HttpResponse(status=404)

        if event == 'unsubscribe':
            list_id = self.get_list_id(data)

            if list_id is None:
                logger.error('Missing list_id in unsubscribe event')
                return HttpResponse(status=200)

            for item in list_id:
                if list_id == settings.BREVO_NEWSLETTER_LIST_ID:
                    self.unsubscribe_user_from_newsletter(user_profile)
        elif event == 'contact_updated':
            content = data['content']
            if content is not None:
                for item in content:
                    if 'deletion' in item['list']:
                        deletions = item['list']['deletion']
                        if deletions is not None:
                            for deletion in deletions:
                                if str(deletion['id']) == settings.BREVO_NEWSLETTER_LIST_ID:
                                    self.unsubscribe_user_from_newsletter(user_profile)

                    if 'addition' in item['list']:
                        additions = item['list']['addition']
                        if additions is not None:
                            for addition in additions:
                                if str(addition['id']) == settings.BREVO_NEWSLETTER_LIST_ID:
                                    self.subscribe_user_to_newsletter(user_profile)

        return HttpResponse(status=200)

    @staticmethod
    def get_event(data: dict) -> str:
        return data['event'] if 'event' in data else None

    @staticmethod
    def get_email(data: dict) -> str:
        return data['email'] if 'email' in data else None

    @staticmethod
    def get_list_id(data: dict) -> str:
        return data['list_id'] if 'list_id' in data else None

    @staticmethod
    def get_user_profile(email: str) -> UserProfile:
        return UserProfile.objects.filter(user__email=email).first()

    @staticmethod
    def unsubscribe_user_from_newsletter(user_profile: UserProfile):
        logger.debug('Unsubscribing user %s from newsletter', user_profile.user.email)
        UserProfile.objects.filter(pk=user_profile.pk).update(receive_newsletter=False)

    @staticmethod
    def subscribe_user_to_newsletter(user_profile: UserProfile):
        logger.debug('Subscribing user %s to newsletter', user_profile.user.email)
        UserProfile.objects.filter(pk=user_profile.pk).update(receive_newsletter=True)

    @staticmethod
    def is_valid_ip(ip):
        valid_ips = ["185.107.232.0/24", "1.179.112.0/20"]
        for valid_ip in valid_ips:
            if ipaddress.ip_address(ip) in ipaddress.ip_network(valid_ip, strict=False):
                return True
        return False
