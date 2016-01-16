# Django
from django.contrib import messages
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import UpdateView

# Third party
from braces.views import LoginRequiredMixin, SuperuserRequiredMixin

# AstroBin
from astrobin.forms import ImageFlagThumbsForm
from astrobin.models import Image


class ImageFlagThumbsView(
        LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    form_class = ImageFlagThumbsForm
    model_class = Image
    pk_url_kwarg = 'id'
    http_method_names = ('post',)

    def get_queryset(self):
        return Image.all_objects.filter(user = self.request.user)

    def get_success_url(self):
        image = self.get_object()
        return reverse_lazy('image_detail', args = (image.pk,))

    def post(self, request, *args, **kwargs):
        image = self.get_object()
        image.thumbnail_invalidate(False)
        for r in image.revisions.all():
            r.thumbnail_invalidate(False)
        messages.success(request, _("Thanks for reporting the problem. All thumbnails will be generated again."))
        return super(ImageFlagThumbsView, self).post(request, args, kwargs)
