from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator

from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import can_download_rawdata
from .utils import rawdata_user_has_valid_subscription


class RestrictToSubscriberMixin(object):
    @method_decorator(user_passes_test(lambda u: rawdata_user_has_valid_subscription(u),
                                       login_url='/rawdata/restricted'))  # TODO: use reverse
    def dispatch(self, *args, **kwargs):
        return super(RestrictToSubscriberMixin, self).dispatch(*args, **kwargs)


class RestrictToCreatorMixin(object):
    def dispatch(self, request, *args, **kwargs):
        obj = get_object_or_404(self.model, pk=kwargs.get('pk'))
        user = request.user

        if user != obj.creator:
            raise Http404

        return super(RestrictToCreatorMixin, self).dispatch(request, *args, **kwargs)


class RestrictToPremiumOrSubscriberMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if not (can_download_rawdata(request.user) and rawdata_user_has_valid_subscription(request.user)):
            raise PermissionDenied

        return super(RestrictToPremiumOrSubscriberMixin, self).dispatch(request, *args, **kwargs)
