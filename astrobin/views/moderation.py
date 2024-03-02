import datetime
import logging

from braces.views import (
    LoginRequiredMixin,
    GroupRequiredMixin,
    JSONResponseMixin,
    SuperuserRequiredMixin,
)
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View
from django.views.generic.list import ListView
from pybb.models import Topic

from astrobin.enums.moderator_decision import ModeratorDecision
from astrobin.models import Image, UserProfile
from astrobin.stories import ACTSTREAM_VERB_UPLOADED_IMAGE, add_story
from astrobin_apps_images.services import ImageService
from astrobin_apps_notifications.tasks import push_notification_for_approved_image, push_notification_for_new_image

log = logging.getLogger(__name__)


class ImageModerationListView(LoginRequiredMixin, GroupRequiredMixin, ListView):
    group_required = "image_moderators"
    raise_exception = True
    model = Image
    template_name = "moderation/image_list.html"

    def get_queryset(self):
        return ImageService().get_images_pending_moderation()


class ImageModerationSpamListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    raise_exception = True
    model = Image
    template_name = "moderation/spam_list.html"

    def get_queryset(self):
        return Image.objects_including_wip.filter(moderator_decision=ModeratorDecision.REJECTED)


class ImageModerationMarkAsSpamView(LoginRequiredMixin, GroupRequiredMixin, JSONResponseMixin, View):
    group_required = "image_moderators"
    raise_exception = True
    methods = "post"

    def post(self, request):
        ids = request.POST.getlist('ids[]')
        Image.objects_including_wip.filter(pk__in=ids).update(
            moderator_decision=ModeratorDecision.REJECTED,
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
            moderator_decision=ModeratorDecision.APPROVED,
            moderated_when=datetime.date.today(),
            moderated_by=request.user)

        for image in Image.objects_including_wip.filter(pk__in=ids):
            push_notification_for_approved_image.apply_async(args=(image.pk, request.user.pk,), countdown=10)
            if not image.is_wip and image.published:
                if not image.skip_notifications:
                    push_notification_for_new_image.apply_async(args=(image.pk,), countdown=10)
                if not image.skip_activity_stream:
                    add_story(image.user, verb=ACTSTREAM_VERB_UPLOADED_IMAGE, action_object=image)

        return self.render_json_response({
            'status': 'OK',
        })


class ImageModerationBanAllView(LoginRequiredMixin, SuperuserRequiredMixin, JSONResponseMixin, View):
    methods = "post"
    raise_exception = True

    def post(self):
        images = Image.objects_including_wip.filter(moderator_decision=ModeratorDecision.REJECTED)
        for i in images:
            i.user.userprofile.delete_reason = UserProfile.DELETE_REASON_IMAGE_SPAM
            i.user.userprofile.save(keep_deleted=True)
            i.user.userprofile.delete()
            log.info("User (%d) was deleted because of image spam" % i.user.pk)

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
                user.userprofile.delete_reason = UserProfile.DELETE_REASON_FORUM_SPAM
                user.userprofile.save(keep_deleted=True)
                user.userprofile.delete()
                log.info("User (%d) was deleted because of forum spam" % user.pk)

            except Topic.DoesNotExist:
                # Topic already deleted by deleting the user
                pass

        messages.success(self.request, _("%s topics deleted") % len(ids))

        referer = reverse("pybb:topic_latest")
        if "HTTP_REFERER" in request.META:
            referer = request.META["HTTP_REFERER"]

        return redirect(referer)
