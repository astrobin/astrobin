# Python
import datetime

# Django
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.views.generic import View
from django.views.generic.list import ListView

# Third party
from braces.views import (
    LoginRequiredMixin,
    GroupRequiredMixin,
    JSONResponseMixin,
    SuperuserRequiredMixin,
)
from toggleproperties.models import ToggleProperty

# AstroBin
from astrobin.models import Image
from astrobin.stories import add_story
from astrobin_apps_notifications.utils import push_notification


class ImageModerationListView(
        LoginRequiredMixin, GroupRequiredMixin, ListView):
    group_required = "image_moderators"
    raise_exception = True
    model = Image
    queryset = Image.all_objects.filter(moderator_decision = 0)
    template_name = "moderation/image_list.html"


class ImageModerationSpamListView(
        LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    raise_exception = True
    model = Image
    queryset = Image.all_objects.filter(moderator_decision = 2)
    template_name = "moderation/spam_list.html"


class ImageModerationMarkAsSpamView(
        LoginRequiredMixin, GroupRequiredMixin, JSONResponseMixin, View):
    group_required = "image_moderators"
    raise_exception = True
    methods = "post"

    def post(self, request, *args, **kwargs):
        ids = request.POST.getlist('ids[]')
        Image.all_objects.filter(pk__in = ids).update(
            moderator_decision = 2,
            moderated_when = datetime.date.today(),
            moderated_by = request.user)

        return self.render_json_response({
            'status': 'OK',
        })


class ImageModerationMarkAsHamView(
        LoginRequiredMixin, GroupRequiredMixin, JSONResponseMixin, View):
    group_required = "image_moderators"
    raise_exception = True
    methods = "post"

    def post(self, request, *args, **kwargs):
        ids = request.POST.getlist('ids[]')
        Image.all_objects.filter(pk__in = ids).update(
            moderator_decision = 1,
            moderated_when = datetime.date.today(),
            moderated_by = request.user)

        for image in Image.all_objects.filter(pk__in = ids):
            if not image.is_wip:
                followers = [x.user for x in ToggleProperty.objects.filter(
                    property_type = "follow",
                    content_type = ContentType.objects.get_for_model(User),
                    object_id = image.user.pk)]

                push_notification(followers, 'new_image',
                    {
                        'object_url': settings.BASE_URL + image.get_absolute_url(),
                        'originator': image.user.userprofile.get_display_name(),
                    })

                add_story(image.user, verb = 'VERB_UPLOADED_IMAGE', action_object = image)


        return self.render_json_response({
            'status': 'OK',
        })


class ImageModerationBanAllView(
        LoginRequiredMixin, SuperuserRequiredMixin, JSONResponseMixin, View):
    methods = "post"
    raise_exception = True

    def post(self, request, *args, **kwargs):
        images = Image.all_objects.filter(moderator_decision = 2)
        for i in images:
            i.user.delete()

        return self.render_json_response({
            'status': 'OK',
        })
