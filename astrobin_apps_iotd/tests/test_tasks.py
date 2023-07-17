from django.conf import settings
from django.contrib.auth.models import Group
from django.test import TestCase
from mock import patch

from astrobin.tests.generators import Generators
from astrobin_apps_iotd.tasks import send_iotd_staff_inactive_reminders_and_remove_after_max_days
from common.constants import GroupName


class IotdTasksTest(TestCase):
    def setUp(self):
        Group.objects.create(name=GroupName.IOTD_STAFF)
        Group.objects.create(name=GroupName.IOTD_SUBMITTERS)
        Group.objects.create(name=GroupName.IOTD_REVIEWERS)

    @patch('astrobin_apps_iotd.tasks.IotdService.get_inactive_submitter_and_reviewers')
    @patch('astrobin_apps_iotd.tasks.push_notification')
    def test_send_iotd_staff_inactive_reminders_and_remove_after_max_days(
            self, push_notification, get_inactive_submitter_and_reviewers):
        submitter = Generators.user(groups=[GroupName.IOTD_STAFF, GroupName.IOTD_SUBMITTERS])
        get_inactive_submitter_and_reviewers.return_value = [submitter]

        send_iotd_staff_inactive_reminders_and_remove_after_max_days()

        groups = submitter.groups.all().values_list('name', flat=True)
        self.assertFalse(GroupName.IOTD_STAFF in groups)
        self.assertFalse(GroupName.IOTD_SUBMITTERS in groups)

        push_notification.assert_called_with([submitter], None, 'iotd_staff_inactive_removal_notice', {
            'BASE_URL': settings.BASE_URL,
            'days': settings.IOTD_MAX_INACTIVE_DAYS,
            'max_inactivity_days': settings.IOTD_MAX_INACTIVE_DAYS
        })
