
from django.test import TestCase

from astrobin_apps_platesolving.backends.pixinsight.solver import Solver
from astrobin_apps_platesolving.models import PlateSolvingAdvancedTask, PlateSolvingAdvancedSettings


class PixInsightSolverTest(TestCase):
    def test_task_params_when_image_smaller_than_hd_in_both_dimensions(self):
        solver = Solver()
        solver.start(
            'http://test.com/test.jpg',
            image_width=1000,
            image_height=1000,
            pixscale=1,
            ra=0,
            dec=0,
            latitude=0,
            longitude=0,
            altitude=0,
            observation_time=None,
            advanced_settings=PlateSolvingAdvancedSettings()
        )

        task = PlateSolvingAdvancedTask.objects.get(pk=1)

        self.assertTrue("largeSize%3D1000" in task.task_params)
        self.assertTrue("smallSizeRatio%3D0.62" in task.task_params)
        self.assertTrue("imageResolution%3D1.00" in task.task_params)

    def test_task_params_when_image_smaller_than_hd_in_h(self):
        solver = Solver()
        solver.start(
            'http://test.com/test.jpg',
            image_width=1000,
            image_height=4000,
            pixscale=1,
            ra=0,
            dec=0,
            latitude=0,
            longitude=0,
            altitude=0,
            observation_time=None,
            advanced_settings=PlateSolvingAdvancedSettings()
        )

        task = PlateSolvingAdvancedTask.objects.get(pk=1)

        self.assertTrue("largeSize%3D4000" in task.task_params)
        self.assertTrue("smallSizeRatio%3D0.62" in task.task_params)
        self.assertTrue("imageResolution%3D1.00" in task.task_params)

    def test_task_params_when_image_smaller_than_hd_in_w(self):
        solver = Solver()
        solver.start(
            'http://test.com/test.jpg',
            image_width=4000,
            image_height=1000,
            pixscale=1,
            ra=0,
            dec=0,
            latitude=0,
            longitude=0,
            altitude=0,
            observation_time=None,
            advanced_settings=PlateSolvingAdvancedSettings()
        )

        task = PlateSolvingAdvancedTask.objects.get(pk=1)

        self.assertTrue("largeSize%3D1824" in task.task_params)
        self.assertTrue("smallSizeRatio%3D0.339" in task.task_params)
        self.assertTrue("imageResolution%3D2.192" in task.task_params)

    def test_task_params_when_image_larger_than_hd_in_both_dimensions(self):
        solver = Solver()
        solver.start(
            'http://test.com/test.jpg',
            image_width=4000,
            image_height=4000,
            pixscale=1,
            ra=0,
            dec=0,
            latitude=0,
            longitude=0,
            altitude=0,
            observation_time=None,
            advanced_settings=PlateSolvingAdvancedSettings()
        )

        task = PlateSolvingAdvancedTask.objects.get(pk=1)

        self.assertTrue("largeSize%3D1824" in task.task_params)
        self.assertTrue("smallSizeRatio%3D0.339" in task.task_params)
        self.assertTrue("imageResolution%3D2.192" in task.task_params)

