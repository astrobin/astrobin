from braces.views import LoginRequiredMixin
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.views.generic import UpdateView

from astrobin_apps_groups.forms import GroupUpdateForm
from astrobin_apps_groups.models import Group
from astrobin_apps_groups.views.mixins import RestrictToGroupOwnerMixin, RedirectToGroupDetailMixin


class GroupUpdateView(LoginRequiredMixin, RestrictToGroupOwnerMixin, RedirectToGroupDetailMixin, UpdateView):
    form_class = GroupUpdateForm
    model = Group
    template_name = 'astrobin_apps_groups/group_update.html'

    def form_valid(self, form):
        group = self.get_object()
        if (group.images.count() > 0 and
                group.autosubmission and
                not form.cleaned_data['autosubmission'] and
                form.cleaned_data['autosubmission_deactivation_strategy'] == 'delete'):
            group.images.clear()
        messages.success(self.request, _("Form saved"))
        return super(GroupUpdateView, self).form_valid(form)
