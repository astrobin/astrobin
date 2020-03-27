from braces.views import LoginRequiredMixin
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.views.generic import CreateView

from astrobin_apps_groups.forms import GroupCreateForm
from astrobin_apps_groups.views.mixins import RedirectToGroupDetailMixin, RestrictToPremiumMembersMixin


class GroupCreateView(LoginRequiredMixin, RedirectToGroupDetailMixin, RestrictToPremiumMembersMixin, CreateView):
    form_class = GroupCreateForm
    template_name = 'astrobin_apps_groups/group_create.html'

    def get_initial(self):
        if 'public' in self.request.GET:
            return {
                'public': self.request.GET.get('public')
            };

        return super(GroupCreateView, self).get_initial()

    def form_valid(self, form):
        group = form.save(commit=False)
        group.creator = self.request.user
        group.owner = self.request.user

        messages.success(self.request, _("Your new group was created successfully"))
        return super(GroupCreateView, self).form_valid(form)
