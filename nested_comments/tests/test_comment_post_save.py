import mock
from django.test import TestCase
from mock import patch

from astrobin.signals import nested_comment_post_save
from astrobin.tests.generators import Generators
from nested_comments.tests.nested_comments_generators import NestedCommentsGenerators


class CommentPostSaveTest(TestCase):
    @patch('astrobin.signals.CommentNotificationsService.send_moderation_required_email_to_superuser')
    @patch('astrobin.signals.CommentNotificationsService.send_notifications')
    @patch('astrobin.signals.push_notification')
    def test_pending_moderation_sends_correct_notifications(
            self, push_notification, send_notifications,
            send_moderation_required_email):
        comment = NestedCommentsGenerators.comment(pending_moderation=True)

        send_moderation_required_email.assert_called()
        send_notifications.assert_not_called()

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(mock.ANY, comment.author, 'new_comment_mention', mock.ANY)

    @patch('astrobin.signals.MentionsService.get_mentions')
    @patch('astrobin.signals.push_notification')
    def test_pending_moderation_does_not_send_mentions(self, push_notification, get_mentions):
        user = Generators.user()
        get_mentions.return_value = [user.get_username()]
        comment = NestedCommentsGenerators.comment(pending_moderation=True)

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(mock.ANY, comment.author, 'new_comment_mention', mock.ANY)

    @patch('astrobin.signals.CommentNotificationsService.send_moderation_required_email_to_superuser')
    @patch('astrobin.signals.CommentNotificationsService.send_notifications')
    @patch('astrobin.signals.push_notification')
    def test_non_pending_moderation_sends_correct_notifications(
            self, push_notification, send_notifications,
            send_moderation_required_email):
        comment = NestedCommentsGenerators.comment()

        send_moderation_required_email.assert_not_called()
        send_notifications.assert_called()

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(mock.ANY, comment.author, 'new_comment_mention', mock.ANY)

    @patch('astrobin.signals.MentionsService.get_mentions')
    @patch('astrobin.signals.push_notification')
    def test_non_pending_moderation_does_send_mentions(self, push_notification, get_mentions):
        user = Generators.user()
        get_mentions.return_value = [user.get_username()]
        comment = NestedCommentsGenerators.comment()

        push_notification.assert_called_with([user], comment.author, 'new_comment_mention', mock.ANY)

    @patch("astrobin.signals.MentionsService.get_mentions")
    @patch("astrobin.signals.CommentNotificationsService.send_notifications")
    @patch("astrobin.signals.CommentNotificationsService.send_moderation_required_notification")
    def test_nested_comment_post_save_sends_moderation_required_notification(
            self, send_moderation_required_notification, send_notifications, get_mentions):
        comment = NestedCommentsGenerators.comment()
        comment.pending_moderation = True

        send_moderation_required_notification.reset_mock()
        send_notifications.reset_mock()
        get_mentions.reset_mock()

        nested_comment_post_save(None, comment, True)

        self.assertTrue(get_mentions.called)
        self.assertFalse(send_notifications.called)
        self.assertTrue(send_moderation_required_notification.called)

        comment.pending_moderation = False

        nested_comment_post_save(None, comment, True)

        self.assertTrue(send_moderation_required_notification.called)
