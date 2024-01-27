from importlib import import_module

from annoying.functions import get_object_or_None
from django.conf import settings

from astrobin_apps_platesolving.backends.astrometry_net.errors import RequestError


class SolverBase(object):
    MISSING = 0
    PENDING = 1
    FAILED = 2
    SUCCESS = 3
    ADVANCED_PENDING = 4
    ADVANCED_FAILED = 5
    ADVANCED_SUCCESS = 6


class Solver(SolverBase):
    def backend(self):
        module_name, backend_name = settings.PLATESOLVING_BACKENDS[0].rsplit('.', 1)
        module = import_module(module_name)
        return getattr(module, backend_name)()

    def solve(self, image_url, **kwargs):
        try:
            return self.backend().start(image_url, **kwargs)
        except RequestError:
            return 0

    def status(self, submission):
        if submission is None or submission == 0:
            return self.MISSING

        try:
            sub_status = self.backend().submission_status(submission)
        except RequestError:
            return self.PENDING

        if sub_status is None:
            return self.PENDING

        if sub_status.get('status', '') == 'fail':
            return self.FAILED

        if 'jobs' in sub_status and not sub_status.get('jobs', []):
            return self.PENDING

        jobs = sub_status.get('jobs', [])
        job = jobs[0]
        if job is None:
            return self.PENDING

        try:
            job_result = self.backend().job_status(job)
        except RequestError:
            return self.PENDING

        status = job_result.get('status')

        if status == 'solving' or status == 'processing':
            return self.PENDING
        elif status == 'success':
            return self.SUCCESS

        return self.FAILED

    def info(self, submission):
        try:
            return self.backend().info(submission)
        except RequestError:
            return {}

    def annotated_image_url(self, submission):
        try:
            return self.backend().annotated_image_url(submission)
        except RequestError:
            return ''

    def annotations(self, submission):
        try:
            return self.backend().annotations(submission)
        except RequestError:
            return None

    def sky_plot_zoom1_image_url(self, submission):
        try:
            return self.backend().sky_plot_zoom1_image_url(submission)
        except RequestError:
            return ''


class AdvancedSolver(SolverBase):
    def backend(self):
        module_name, backend_name = settings.PLATESOLVING_BACKENDS[1].rsplit('.', 1)
        module = import_module(module_name)
        return getattr(module, backend_name)()

    def solve(self, image_url, **kwargs):
        return self.backend().start(image_url, **kwargs)

    def status(self, submission):
        solution = get_object_or_None(
            "astrobin_apps_platesolving.models.Solution",
            pixinsight_serial_number=submission)

        if solution is None:
            return self.ADVANCED_PENDING

        return solution.status
