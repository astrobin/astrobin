from datetime import datetime, timedelta

import mock
from django.conf import settings
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from mock import patch

from astrobin.models import Image
from astrobin.tests.generators import Generators
from astrobin_apps_iotd.models import IotdSubmitterSeenImage
from astrobin_apps_iotd.tasks import (
    resubmit_images_for_iotd_tp_consideration_if_they_did_not_get_enough_views,
    send_iotd_staff_inactive_reminders_and_remove_after_max_days, send_notifications_when_promoted_image_becomes_iotd,
)
from astrobin_apps_iotd.tests.iotd_generators import IotdGenerators
from common.constants import GroupName
from common.utils import make_custom_cache_get_side_effect


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

    @patch('astrobin_apps_iotd.tasks.IotdService.get_recently_expired_unsubmitted_images')
    @patch('astrobin_apps_iotd.tasks.IotdService.resubmit_to_iotd_tp_process')
    def test_resubmit_images_for_iotd_tp_consideration_if_they_did_not_get_enough_views_not_called(
            self,
            resubmit_to_iotd_tp_process,
            get_recently_expired_unsubmitted_images
    ):
        image = Generators.image()
        image.submitted_for_iotd_tp_consideration = datetime.now() - timedelta(1)
        image.save()

        submitters = []

        for x in range(0, 10):
            submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
            submitters.append(submitter)
            IotdSubmitterSeenImage.objects.create(user=submitter, image=image)

        get_recently_expired_unsubmitted_images.return_value = Image.objects.filter(pk=image.pk)

        resubmit_images_for_iotd_tp_consideration_if_they_did_not_get_enough_views()

        resubmit_to_iotd_tp_process.assert_not_called()

    @patch('astrobin_apps_iotd.tasks.IotdService.get_recently_expired_unsubmitted_images')
    @patch('astrobin_apps_iotd.tasks.IotdService.resubmit_to_iotd_tp_process')
    def test_resubmit_images_for_iotd_tp_consideration_if_they_did_not_get_enough_views_called(
            self,
            resubmit_to_iotd_tp_process,
            get_recently_expired_unsubmitted_images
    ):
        image = Generators.image()
        image.submitted_for_iotd_tp_consideration = datetime.now() - timedelta(1)
        image.save()

        submitters = []

        for x in range(0, 10):
            submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
            submitters.append(submitter)
            if x < 3:
                IotdSubmitterSeenImage.objects.create(user=submitter, image=image)

        get_recently_expired_unsubmitted_images.return_value = Image.objects.filter(pk=image.pk)

        resubmit_images_for_iotd_tp_consideration_if_they_did_not_get_enough_views()

        resubmit_to_iotd_tp_process.assert_called()

    @patch('astrobin_apps_iotd.tasks.IotdService.get_recently_expired_unsubmitted_images')
    @patch('astrobin_apps_iotd.tasks.IotdService.resubmit_to_iotd_tp_process')
    @patch(
        'astrobin_apps_iotd.tasks.cache.get',
        side_effect=make_custom_cache_get_side_effect('last_iotd_tp_resubmission_check', None)
    )
    def test_resubmit_images_for_iotd_tp_consideration_with_last_check_None(
            self,
            cache_get,
            resubmit_to_iotd_tp_process,
            get_recently_expired_unsubmitted_images,
    ):
        image = Generators.image()
        image.submitted_for_iotd_tp_consideration = datetime.now() - timedelta(1)
        image.save()

        submitters = []

        for x in range(0, 10):
            submitter = Generators.user(groups=[GroupName.IOTD_SUBMITTERS])
            submitters.append(submitter)
            if x < 3:
                IotdSubmitterSeenImage.objects.create(user=submitter, image=image)

        get_recently_expired_unsubmitted_images.return_value = Image.objects.filter(pk=image.pk)

        resubmit_images_for_iotd_tp_consideration_if_they_did_not_get_enough_views()

        resubmit_to_iotd_tp_process.assert_called()
        get_recently_expired_unsubmitted_images.assert_called_with(timedelta(hours=1))

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=1)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=1)
    @patch('astrobin_apps_iotd.tasks.push_notification')
    def test_send_notifications_when_promoted_image_becomes_iotd_with_collaborators(self, push_notification):
        image = Generators.image(submitted_for_iotd_tp_consideration=datetime.now() - timedelta(1))
        collaborator = Generators.user()
        image.collaborators.add(collaborator)
        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.iotd(image=image)

        send_notifications_when_promoted_image_becomes_iotd()

        push_notification.assert_called_with(
            [image.user, collaborator],
            None,
            'your_image_is_iotd',
            mock.ANY
        )

    @override_settings(IOTD_SUBMISSION_MIN_PROMOTIONS=1)
    @override_settings(IOTD_REVIEW_MIN_PROMOTIONS=1)
    @patch('astrobin_apps_iotd.tasks.push_notification')
    def test_send_notifications_when_promoted_image_becomes_iotd_without_collaborators(self, push_notification):
        image = Generators.image(submitted_for_iotd_tp_consideration=datetime.now() - timedelta(1))
        IotdGenerators.submission(image=image)
        IotdGenerators.vote(image=image)
        IotdGenerators.iotd(image=image)

        send_notifications_when_promoted_image_becomes_iotd()

        push_notification.assert_called_with(
            [image.user],
            None,
            'your_image_is_iotd',
            mock.ANY
        )
