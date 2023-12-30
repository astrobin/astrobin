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
from django.utils.translation import gettext
from django.views import View
from django.views.generic import base
from django_bouncy.models import Bounce, Complaint

from astrobin.models import UserProfile
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


class BrevoWebhook(View):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs) -> HttpResponse:
        data = json.loads(request.body.decode('utf-8'))

        if data['api_key'] != settings.BREVO_API_KEY:
            logger.error('Invalid Brevo API key')
            return HttpResponseForbidden()

        if data['event'] == 'unsubscribe':
            email = data['email']
            user_profile = UserProfile.objects.filter(user__email=email).first()
            list_id = data['list_id']

            logger.info('Unsubscribing %s from list %s', email, list_id)

            if user_profile and list_id == settings.BREVO_NEWSLETTER_LIST_ID:
                user_profile.receive_newsletter = False
                user_profile.save(keep_deleted=False)

        return HttpResponse(status=200)
