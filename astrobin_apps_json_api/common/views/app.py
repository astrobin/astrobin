from os.path import abspath, dirname, join

from braces.views import JSONResponseMixin
from django.views.generic.base import View

from common.utils import get_project_root


class AppConfig(JSONResponseMixin, View):
    def get(self, request, *args, **kwargs):
        version_file = join(get_project_root(), 'VERSION')  # type: str

        f = open(version_file, 'r')
        version = f.read().strip()
        f.close()

        return self.render_json_response({u"version": version})
