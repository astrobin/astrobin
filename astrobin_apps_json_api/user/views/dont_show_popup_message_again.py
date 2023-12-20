from braces.views import JsonRequestResponseMixin
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from astrobin.models import PopupMessage, PopupMessageUserStatus


@method_decorator(csrf_exempt, name='dispatch')
class DontShowPopupMessageAgain(JsonRequestResponseMixin, View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()

        popup_id = request.POST.get("popup_id")

        popup_message = get_object_or_404(PopupMessage, id=popup_id)

        PopupMessageUserStatus.objects.get_or_create(
            user=request.user,
            popup_message=popup_message,
            seen=timezone.now(),
        )

        return self.render_json_response({"status": "OK"})
