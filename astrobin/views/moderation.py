# Python
import datetime

# Django
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View
from django.views.generic.list import ListView

# Third party
from braces.views import (
    LoginRequiredMixin,
    GroupRequiredMixin,
    JSONResponseMixin,
    SuperuserRequiredMixin,
)
from pybb.models import Topic
from toggleproperties.models import ToggleProperty

# AstroBin
from astrobin.models import Image
from astrobin.stories import add_story
from astrobin_apps_notifications.utils import push_notification


class ImageModerationListView(LoginRequiredMixin, GroupRequiredMixin, ListView):
    group_required = "image_moderators"
    raise_exception = True
    model = Image
    queryset = Image.objects_including_wip.filter(moderator_decision=0)
    template_name = "moderation/image_list.html"


class ImageModerationSpamListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    raise_exception = True
    model = Image
    queryset = Image.objects_including_wip.filter(moderator_decision=2)
    template_name = "moderation/spam_list.html"


class ImageModerationMarkAsSpamView(LoginRequiredMixin, GroupRequiredMixin, JSONResponseMixin, View):
    group_required = "image_moderators"
    raise_exception = True
    methods = "post"

    def post(self, request):
        ids = request.POST.getlist('ids[]')
        Image.objects_including_wip.filter(pk__in=ids).update(
            moderator_decision=2,
            moderated_when=datetime.date.today(),
            moderated_by=request.user)

        return self.render_json_response({
            'status': 'OK',
        })


class ImageModerationMarkAsHamView(LoginRequiredMixin, GroupRequiredMixin, JSONResponseMixin, View):
    group_required = "image_moderators"
    raise_exception = True
    methods = "post"

    def post(self, request):
        ids = request.POST.getlist('ids[]')
        Image.objects_including_wip.filter(pk__in=ids).update(
            moderator_decision=1,
            moderated_when=datetime.date.today(),
            moderated_by=request.user)

        for image in Image.objects_including_wip.filter(pk__in=ids):
            if not image.is_wip:
                followers = [x.user for x in ToggleProperty.objects.filter(
                    property_type="follow",
                    content_type=ContentType.objects.get_for_model(User),
                    object_id=image.user.pk)]

                thumb = image.thumbnail_raw('gallery', {'sync': True})
                push_notification(followers, 'new_image', {
                    'image': image,
                    'image_thumbnail': thumb.url if thumb else None
                })

                add_story(image.user, verb='VERB_UPLOADED_IMAGE', action_object=image)

        return self.render_json_response({
            'status': 'OK',
        })


class ImageModerationBanAllView(LoginRequiredMixin, SuperuserRequiredMixin, JSONResponseMixin, View):
    methods = "post"
    raise_exception = True

    def post(self):
        images = Image.objects_including_wip.filter(moderator_decision=2)
        for i in images:
            i.user.userprofile.delete()

        return self.render_json_response({
            'status': 'OK',
        })


class ForumModerationMarkAsSpamView(LoginRequiredMixin, GroupRequiredMixin, View):
    group_required = "content_moderators"
    raise_exception = True
    methods = "post"

    def post(self, request):
        ids = request.POST.getlist('topic-ids[]')

        for id in ids:
            try:
                topic = Topic.objects.get(id=id)
                user = topic.user
                user.userprofile.delete()
            except Topic.DoesNotExist:
                # Topic already deleted by deleting the user
                pass

        messages.success(self.request, _("%s topics deleted") % len(ids))

        referer = reverse("pybb:topic_latest")
        if "HTTP_REFERER" in request.META:
            referer = request.META["HTTP_REFERER"]

        return redirect(referer)
