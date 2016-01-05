# Python
import simplejson as json

# Django
from django.contrib.auth.decorators import user_passes_test
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator

# This app
from .utils import rawdata_user_has_valid_subscription


class RestrictToSubscriberMixin(object):
    @method_decorator(user_passes_test(lambda u: rawdata_user_has_valid_subscription(u),
                                       login_url = '/rawdata/restricted')) #TODO: use reverse
    def dispatch(self, *args, **kwargs):
        return super(RestrictToSubscriberMixin, self).dispatch(*args, **kwargs)


class RestrictToCreatorMixin(object):
    def dispatch(self, request, *args, **kwargs):
        obj = get_object_or_404(self.model, pk = kwargs.get('pk'))
        user = request.user

        if user != obj.creator:
            raise Http404

        return super(RestrictToCreatorMixin, self).dispatch(request, *args, **kwargs)
