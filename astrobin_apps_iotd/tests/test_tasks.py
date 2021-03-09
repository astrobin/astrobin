from django.conf import settings
from django.contrib.auth.models import Group
from django.test import TestCase
from mock import patch

from astrobin.tests.generators import Generators
from astrobin_apps_iotd.tasks import send_iotd_staff_inactive_reminders_and_remove_after_max_days


class IotdTasksTest(TestCase):
    def setUp(self):
        Group.objects.create(name='iotd_staff')
        Group.objects.create(name='iotd_submitters')
        Group.objects.create(name='iotd_reviewers')

    @patch('astrobin_apps_iotd.tasks.IotdService.get_inactive_submitter_and_reviewers')
    @patch('astrobin_apps_iotd.tasks.push_notification')
    def test_send_iotd_staff_inactive_reminders_and_remove_after_max_days(
            self, push_notification, get_inactive_submitter_and_reviewers):
        submitter = Generators.user(groups=['iotd_staff', 'iotd_submitters'])
        get_inactive_submitter_and_reviewers.return_value = [submitter]

        send_iotd_staff_inactive_reminders_and_remove_after_max_days()

        groups = submitter.groups.all().values_list('name', flat=True)
        self.assertFalse('iotd_staff' in groups)
        self.assertFalse('iotd_submitters' in groups)

        push_notification.assert_called_with([submitter], 'iotd_staff_inactive_removal_notice', {
            'BASE_URL': settings.BASE_URL,
            'days': settings.IOTD_MAX_INACTIVE_DAYS,
            'max_inactivity_days': settings.IOTD_MAX_INACTIVE_DAYS
        })
