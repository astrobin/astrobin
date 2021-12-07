from unittest.mock import patch

from django.test import TestCase

from astrobin.tests.generators import Generators
from astrobin_apps_iotd.templatetags.astrobin_apps_iotd_tags import (
    may_submit_to_iotd_tp_process,
    may_submit_to_iotd_tp_process_reason,
)


class TagsTest(TestCase):
    @patch('astrobin_apps_iotd.templatetags.astrobin_apps_iotd_tags.IotdService.may_submit_to_iotd_tp_process')
    def test_may_submit_to_iotd_tp_process_may(self, may_submit_to_iotd_tp_process_service):
        may_submit_to_iotd_tp_process_service.return_value = True, None

        image = Generators.image()

        self.assertTrue(may_submit_to_iotd_tp_process(image.user, image))

    @patch('astrobin_apps_iotd.templatetags.astrobin_apps_iotd_tags.IotdService.may_submit_to_iotd_tp_process')
    def test_may_submit_to_iotd_tp_process_reason(self, may_submit_to_iotd_tp_process_service):
        may_submit_to_iotd_tp_process_service.return_value = False, 'ALREADY_SUBMITTED'

        image = Generators.image()

        self.assertEqual('ALREADY_SUBMITTED', may_submit_to_iotd_tp_process_reason(image.user, image))
