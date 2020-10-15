from django.conf import settings
from django.http import HttpResponse, Http404
from django.views.generic import View


class AdsTxtView(View):
    def get(self, request):
        publisher = settings.ADSENSE_PUBLISHER_ID
        if settings.ADSENSE_ENABLED and publisher:
            return HttpResponse(
                "google.com, pub-%s, DIRECT, f08c47fec0942fa0" % publisher,
                content_type='text/plain')

        raise Http404
