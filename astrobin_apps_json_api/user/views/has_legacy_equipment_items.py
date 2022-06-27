from braces.views import JsonRequestResponseMixin
from django.contrib.auth.models import User
from django.views import View
from rest_framework.generics import get_object_or_404

from astrobin.services.gear_service import GearService


class HasLegacyGear(JsonRequestResponseMixin, View):
    def get(self, request):
        userId: str = request.GET.get('userId')
        user: User = get_object_or_404(User, id=userId)
        return self.render_json_response(dict(result=GearService.has_unmigrated_legacy_gear_items(user)))
