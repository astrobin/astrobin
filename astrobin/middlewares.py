import sys
import cProfile
from cStringIO import StringIO
from django.conf import settings

from django.middleware.cache import CacheMiddleware


class ProfilerMiddleware(object):
    def process_view(self, request, callback, callback_args, callback_kwargs):
        if settings.DEBUG and 'prof' in request.GET:
            self.profiler = cProfile.Profile()
            args = (request,) + callback_args
            return self.profiler.runcall(callback, *args, **callback_kwargs)

    def process_response(self, request, response):
        if settings.DEBUG and 'prof' in request.GET:
            self.profiler.create_stats()
            out = StringIO()
            old_stdout, sys.stdout = sys.stdout, out
            self.profiler.print_stats(1)
            sys.stdout = old_stdout
            response.content = '<pre>%s</pre>' % out.getvalue()
        return response

class VaryOnLangCacheMiddleware(CacheMiddleware):
    def __init__(self, **kwargs):
        CacheMiddleware.__init__(self, **kwargs)
        self.ori_key_prefix = self.key_prefix

    def process_request(self, request):
        # Reset key_prefix depending on language
        lang_suffix = '_%s' % request.LANGUAGE_CODE
        if not self.key_prefix.endswith(lang_suffix):
            self.key_prefix = self.ori_key_prefix + lang_suffix
        return CacheMiddleware.process_request(self, request)

