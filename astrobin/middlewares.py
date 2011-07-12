from django.http import HttpResponseRedirect
from django.conf import settings

class ComingSoonMiddleware:
    def process_request(self, request):
        if settings.ASTROBIN_COMING_SOON:
            if request.path_info != settings.ASTROBIN_COMING_SOON_URL: 
                return HttpResponseRedirect(settings.ASTROBIN_COMING_SOON_URL)

