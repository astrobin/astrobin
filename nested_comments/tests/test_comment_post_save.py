import mock
from django.test import TestCase
from mock import patch

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
