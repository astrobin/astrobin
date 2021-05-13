from django.test import TestCase
from mock import patch

from astrobin.signals import imagerevision_post_save, nested_comment_post_save
from astrobin.tests.generators import Generators
from nested_comments.tests.nested_comments_generators import NestedCommentsGenerators


class SignalsTest(TestCase):

    @patch("astrobin.signals.push_notification")
    @patch("astrobin.signals.add_story")
    def test_imagerevision_post_save_wip_no_notifications(self, add_story, push_notification):
        revision = Generators.imageRevision()
        revision.image.is_wip = True

        push_notification.reset_mock()
        add_story.reset_mock()

        imagerevision_post_save(None, revision, True)

        self.assertFalse(push_notification.called)
        self.assertFalse(add_story.called)

    @patch("astrobin.signals.push_notification")
    @patch("astrobin.signals.add_story")
    def test_imagerevision_post_save_not_created_no_notifications(self, add_story, push_notification):
        revision = Generators.imageRevision()

        push_notification.reset_mock()
        add_story.reset_mock()

        imagerevision_post_save(None, revision, False)

        self.assertFalse(push_notification.called)
        self.assertFalse(add_story.called)

    @patch("astrobin.signals.push_notification")
    @patch("astrobin.signals.add_story")
    def test_imagerevision_post_save_skip_notifications(self, add_story, push_notification):
        revision = Generators.imageRevision()
        revision.skip_notifications = True

        push_notification.reset_mock()
        add_story.reset_mock()

        imagerevision_post_save(None, revision, True)

        self.assertFalse(push_notification.called)
        self.assertFalse(add_story.called)

    @patch("astrobin.signals.add_story")
    def test_imagerevision_post_save(self, add_story):
        revision = Generators.imageRevision()

        add_story.reset_mock()

        imagerevision_post_save(None, revision, True)

        self.assertTrue(add_story.called)

    @patch("astrobin.signals.MentionsService.get_mentions")
    @patch("astrobin.signals.CommentNotificationsService.send_notifications")
    @patch("astrobin.signals.CommentNotificationsService.send_moderation_required_email")
    def test_nested_comment_post_save_sends_moderation_required_email(
            self, send_moderation_required_email, send_notifications, get_mentions):
        comment = NestedCommentsGenerators.comment()
        comment.pending_moderation = True

        nested_comment_post_save(None, comment, True)

        self.assertTrue(get_mentions.called)
        self.assertTrue(send_notifications.called)
        self.assertTrue(send_moderation_required_email.called)

        comment.pending_moderation = False

        nested_comment_post_save(None, comment, True)

        self.assertTrue(send_moderation_required_email.called)
