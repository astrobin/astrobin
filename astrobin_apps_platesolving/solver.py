from importlib import import_module

from django.conf import settings


class Solver(object):
    FAIL    = 0
    SOLVING = 1
    SUCCESS = 2

    def _backend(self):
        module_name, backend_name = \
            settings.ASTROBIN_PLATESOLVING_BACKEND.rsplit('.', 1)

        print module_name, backend_name

        module = import_module(module_name)
        return getattr(module, backend_name)()

    # Starts the job and returns an id for later reference
    def solve(self, image):
        return self._backend().start(image)

    def status(self, submission):
        sub_status = self._backend().sub_status(submission)
        status = sub_status.get('status')
        if status == 'fail':
            return self.FAIL

        jobs = sub_status.get('jobs', [])
        if not jobs:
            return self.SOLVING

        job = jobs[0]
        job_result = self._backend().job_status(job)
        status = job_result.get('status')
        if status == 'solving':
            return self.SOLVING
        elif status == 'success':
            return self.SUCCESS

        return self.FAIL

