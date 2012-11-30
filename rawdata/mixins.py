# Python
import simplejson as json

# Django
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.utils.decorators import method_decorator

# This app
from .utils import user_has_active_subscription


class AjaxableResponseMixin(object):
    """
    Mixin to add AJAX support to a form.
    Must be used with an object-based FormView (e.g. CreateView)
    """
    def render_to_json_response(self, context, **response_kwargs):
        data = json.dumps(context)
        response_kwargs['content_type'] = 'application/json'
        return HttpResponse(data, **response_kwargs)

    def form_invalid(self, form):
        if self.request.is_ajax():
            return self.render_to_json_response(form.errors, status=400)
        else:
            return super(AjaxableResponseMixin, self).form_invalid(form)

    def form_valid(self, form):
        if self.request.is_ajax():
            data = {
                'pk': form.instance.pk,
            }
            return self.render_to_json_response(data)
        else:
            return super(AjaxableResponseMixin, self).form_valid(form)


class RestrictToSubscriberMixin(object):
    @method_decorator(user_passes_test(lambda u: user_has_active_subscription(u)))
    def dispatch(self, *args, **kwargs):
        return super(RestrictToSubscriberMixin, self).dispatch(*args, **kwargs)
