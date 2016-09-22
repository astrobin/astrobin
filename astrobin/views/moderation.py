# Python
import datetime

# Django
from django.views.generic import View
from django.views.generic.list import ListView

# Third party
from braces.views import (
    LoginRequiredMixin,
    GroupRequiredMixin,
    JSONResponseMixin,
)

# AstroBin
from astrobin.models import Image


class ImageModerationListView(
        LoginRequiredMixin, ListView, GroupRequiredMixin):
    group_required = "Content moderators"
    model = Image
    queryset = Image.all_objects.filter(moderator_decision = 0)
    template_name = "moderation/image_list.html"


class ImageModerationSpamListView(
        LoginRequiredMixin, ListView, GroupRequiredMixin):
    group_required = "Content moderators"
    model = Image
    queryset = Image.all_objects.filter(moderator_decision = 2)
    template_name = "moderation/spam_list.html"


class ImageModerationMarkAsSpamView(
        LoginRequiredMixin, GroupRequiredMixin, JSONResponseMixin, View):
    group_required = "Content moderators"
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
    group_required = "Content moderators"
    methods = "post"

    def post(self, request, *args, **kwargs):
        ids = request.POST.getlist('ids[]')
        Image.all_objects.filter(pk__in = ids).update(
            moderator_decision = 1,
            moderated_when = datetime.date.today(),
            moderated_by = request.user)

        return self.render_json_response({
            'status': 'OK',
        })


class ImageModerationBanAllView(
        LoginRequiredMixin, GroupRequiredMixin, JSONResponseMixin, View):
    group_required = "Content moderators"
    methods = "post"

    def post(self, request, *args, **kwargs):
        images = Image.all_objects.filter(moderator_decision = 2)
        for i in images:
            i.user.delete()

        return self.render_json_response({
            'status': 'OK',
        })
