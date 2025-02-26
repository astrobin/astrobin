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
    send_iotd_staff_inactive_reminders_and_remove_after_max_days, 
    send_notifications_when_promoted_image_becomes_iotd,
    send_iotd_staff_insufficiently_active_reminders_and_remove_after_max_reminders,
)
from astrobin_apps_iotd.tests.iotd_generators import IotdGenerators
from astrobin_apps_notifications.services.notifications_service import NotificationContext
from common.constants import GroupName
from common.utils import make_custom_cache_get_side_effect


class IotdTasksTest(TestCase):
    def setUp(self):
        Group.objects.create(name=GroupName.IOTD_STAFF)
        Group.objects.create(name=GroupName.IOTD_SUBMITTERS)
        Group.objects.create(name=GroupName.IOTD_REVIEWERS)

    @patch('astrobin_apps_iotd.tasks.mail_admins')
    @patch('astrobin_apps_iotd.tasks.IotdService.get_inactive_submitters_and_reviewers')
    @patch('astrobin_apps_iotd.tasks.push_notification')
    def test_send_iotd_staff_inactive_reminders_and_remove_after_max_days(
            self,
            push_notification,
            get_inactive_submitter_and_reviewers,
            mail_admins
    ):
        submitter = Generators.user(groups=[GroupName.IOTD_STAFF, GroupName.IOTD_SUBMITTERS])
        get_inactive_submitter_and_reviewers.return_value = [submitter]

        send_iotd_staff_inactive_reminders_and_remove_after_max_days()

        groups = submitter.groups.all().values_list('name', flat=True)
        self.assertFalse(GroupName.IOTD_STAFF in groups)
        self.assertFalse(GroupName.IOTD_SUBMITTERS in groups)

        push_notification.assert_called_with([submitter], None, 'iotd_staff_inactive_removal_notice', {
            'BASE_URL': settings.BASE_URL,
            'days': settings.IOTD_MAX_INACTIVE_DAYS,
            'max_inactivity_days': settings.IOTD_MAX_INACTIVE_DAYS,
            'extra_tags': { 'context': NotificationContext.IOTD }
        })
        
        # Verify that mail_admins was called with the correct arguments
        mail_admins.assert_called_with(
            subject=f"IOTD: {submitter.username} (Submitter) removed from staff due to inactivity",
            message=f"User {submitter.username} (ID: {submitter.pk}) has been removed from the IOTD staff groups.\n\n"
                    f"Role(s): Submitter\n\n"
                    f"Reason: They have been inactive for {settings.IOTD_MAX_INACTIVE_DAYS} days."
        )

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
        get_recently_expired_unsubmitted_images.assert_called_with(timedelta(hours=2))

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
        
    @patch('astrobin_apps_iotd.tasks.mail_admins')
    @patch('astrobin_apps_iotd.tasks.IotdService.get_insufficiently_active_submitters_and_reviewers')
    @patch('astrobin_apps_iotd.tasks.push_notification')
    def test_send_iotd_staff_insufficiently_active_reminders_and_remove_after_max_reminders_submitter(
            self,
            push_notification,
            get_insufficiently_active_members,
            mail_admins
    ):
        submitter = Generators.user(groups=[GroupName.IOTD_STAFF, GroupName.IOTD_SUBMITTERS])
        submitter.userprofile.insufficiently_active_iotd_staff_member_reminders_sent = 2
        submitter.userprofile.save()
        
        get_insufficiently_active_members.return_value = [submitter]

        # Call the task being tested
        send_iotd_staff_insufficiently_active_reminders_and_remove_after_max_reminders()

        # Check that user was removed from groups
        groups = submitter.groups.all().values_list('name', flat=True)
        self.assertFalse(GroupName.IOTD_STAFF in groups)
        self.assertFalse(GroupName.IOTD_SUBMITTERS in groups)

        # Check that push_notification was called with correct args
        push_notification.assert_called_with(
            [submitter], None, 'iotd_staff_inactive_removal_notice', mock.ANY
        )
        
        # Verify that mail_admins was called with the correct arguments
        mail_admins.assert_called_with(
            subject=f"IOTD: {submitter.username} (Submitter) removed from staff due to inactivity",
            message=f"User {submitter.username} (ID: {submitter.pk}) has been removed from the IOTD staff groups.\n\n"
                    f"Role(s): Submitter\n\n"
                    f"Reason: They did not meet the minimum requirement of 14 promotions in 7 days "
                    f"after receiving 2 reminders."
        )
        
    @patch('astrobin_apps_iotd.tasks.mail_admins')
    @patch('astrobin_apps_iotd.tasks.IotdService.get_insufficiently_active_submitters_and_reviewers')
    def test_send_iotd_staff_insufficiently_active_reminders_and_remove_after_max_reminders_reviewer(
            self,
            get_insufficiently_active_members,
            mail_admins
    ):
        reviewer = Generators.user(groups=[GroupName.IOTD_STAFF, GroupName.IOTD_REVIEWERS])
        reviewer.userprofile.insufficiently_active_iotd_staff_member_reminders_sent = 2
        reviewer.userprofile.save()
        
        get_insufficiently_active_members.return_value = [reviewer]

        # Call the task being tested
        send_iotd_staff_insufficiently_active_reminders_and_remove_after_max_reminders()

        # Check that user was removed from groups
        groups = reviewer.groups.all().values_list('name', flat=True)
        self.assertFalse(GroupName.IOTD_STAFF in groups)
        self.assertFalse(GroupName.IOTD_REVIEWERS in groups)

        # Verify that mail_admins was called with the correct arguments
        mail_admins.assert_called_with(
            subject=f"IOTD: {reviewer.username} (Reviewer) removed from staff due to inactivity",
            message=f"User {reviewer.username} (ID: {reviewer.pk}) has been removed from the IOTD staff groups.\n\n"
                    f"Role(s): Reviewer\n\n"
                    f"Reason: They did not meet the minimum requirement of 14 promotions in 7 days "
                    f"after receiving 2 reminders."
        )
        
    @patch('astrobin_apps_iotd.tasks.mail_admins')
    @patch('astrobin_apps_iotd.tasks.IotdService.get_insufficiently_active_submitters_and_reviewers')
    def test_send_iotd_staff_insufficiently_active_reminders_and_remove_after_max_reminders_both_roles(
            self,
            get_insufficiently_active_members,
            mail_admins
    ):
        member = Generators.user(groups=[GroupName.IOTD_STAFF, GroupName.IOTD_SUBMITTERS, GroupName.IOTD_REVIEWERS])
        member.userprofile.insufficiently_active_iotd_staff_member_reminders_sent = 2
        member.userprofile.save()
        
        get_insufficiently_active_members.return_value = [member]

        # Call the task being tested
        send_iotd_staff_insufficiently_active_reminders_and_remove_after_max_reminders()

        # Check that user was removed from all groups
        groups = member.groups.all().values_list('name', flat=True)
        self.assertFalse(GroupName.IOTD_STAFF in groups)
        self.assertFalse(GroupName.IOTD_SUBMITTERS in groups)
        self.assertFalse(GroupName.IOTD_REVIEWERS in groups)

        # Verify that mail_admins was called with the correct arguments - both roles should be mentioned
        mail_admins.assert_called_with(
            subject=f"IOTD: {member.username} (Submitter and Reviewer) removed from staff due to inactivity",
            message=f"User {member.username} (ID: {member.pk}) has been removed from the IOTD staff groups.\n\n"
                    f"Role(s): Submitter and Reviewer\n\n"
                    f"Reason: They did not meet the minimum requirement of 14 promotions in 7 days "
                    f"after receiving 2 reminders."
        )
