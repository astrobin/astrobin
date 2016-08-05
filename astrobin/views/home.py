# Django
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.views.generic import View

# Third party
from braces.views import LoginRequiredMixin

# AstroBin
from astrobin.models import UserProfile


class HomeSetDefaultSectionView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        section = kwargs['section']
        profile = request.user.userprofile
        profile.default_frontpage_section = section
        profile.save()

        messages.success(request, _("Default front page section changed."))
        return HttpResponseRedirect(reverse('index'))
