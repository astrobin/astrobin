from importlib import import_module

from django.conf import settings


class Solver(object):
    MISSING = 0
    PENDING = 1
    FAILED  = 2
    SUCCESS = 3

    def _backend(self):
        module_name, backend_name = \
            settings.ASTROBIN_PLATESOLVING_BACKEND.rsplit('.', 1)

        print module_name, backend_name

        module = import_module(module_name)
        return getattr(module, backend_name)()

    # Starts the job and returns an id for later reference
    def solve(self, image_file):
        return self._backend().start(image_file)

    def status(self, submission):
        if submission is None or submission == 0:
            return self.MISSING

        sub_status = self._backend().sub_status(submission)
        status = sub_status.get('status')
        if status == 'fail':
            return self.FAILED

        jobs = sub_status.get('jobs', [])
        if not jobs:
            return self.PENDING

        job = jobs[0]
        job_result = self._backend().job_status(job)
        status = job_result.get('status')
        if status == 'solving':
            return self.PENDING
        elif status == 'success':
            return self.SUCCESS

        return self.FAIL

