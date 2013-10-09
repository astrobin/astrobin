from importlib import import_module

from django.conf import settings


class Solver(object):
    def _backend(self):
        module_name, backend_name = \
            settings.ASTROBIN_PLATESOLVING_BACKEND.rsplit('.', 1)

        print module_name, backend_name

        module = import_module(module_name)
        return getattr(module, backend_name)()

    # Starts the job and returns an id for later reference
    def solve(self, image):
        backend = self._backend()
        return backend.start(image)
