import mock
from django.test import TestCase
from mock import patch

from astrobin.tests.generators import Generators
from nested_comments.tests.nested_comments_generators import NestedCommentsGenerators


class CommentNotificationServiceTest(TestCase):
    @patch("astrobin.models.UserProfile.get_scores")
    @patch("nested_comments.services.comment_notifications_service.push_notification")
    @patch("nested_comments.services.comment_notifications_service.add_story")
    def test_send_notifications_pending_moderation(self, add_story, push_notification, get_scores):
        get_scores.return_value = {'user_scores_index': .5}
        comment = NestedCommentsGenerators.comment()

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(mock.ANY, 'new_comment', mock.ANY)

        with self.assertRaises(AssertionError):
            add_story.assert_called_with(
                comment.author, verb='VERB_COMMENTED_IMAGE',
                action_object=comment,
                target=comment.content_object)

    @patch("astrobin.models.UserProfile.get_scores")
    @patch("nested_comments.services.comment_notifications_service.push_notification")
    @patch("nested_comments.services.comment_notifications_service.add_story")
    def test_send_notifications_shadowban(self, add_story, push_notification, get_scores):
        get_scores.return_value = {'user_scores_index': 2}

        image = Generators.image()
        shadowbanned_user = Generators.user()

        image.user.userprofile.shadow_bans.add(shadowbanned_user.userprofile)

        comment = NestedCommentsGenerators.comment(author=shadowbanned_user, target=image)

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(mock.ANY, 'new_comment', mock.ANY)

        with self.assertRaises(AssertionError):
            add_story.assert_called_with(
                comment.author, verb='VERB_COMMENTED_IMAGE',
                action_object=comment,
                target=comment.content_object)

    @patch("astrobin.models.UserProfile.get_scores")
    @patch("nested_comments.services.comment_notifications_service.push_notification")
    @patch("nested_comments.services.comment_notifications_service.add_story")
    def test_send_notifications_wip(self, add_story, push_notification, get_scores):
        get_scores.return_value = {'user_scores_index': 2}

        image = Generators.image(is_wip=True)
        commenter = Generators.user()

        comment = NestedCommentsGenerators.comment(author=commenter, target=image)

        push_notification.assert_called_with(mock.ANY, 'new_comment', mock.ANY)

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(mock.ANY, 'new_comment_reply', mock.ANY)

        with self.assertRaises(AssertionError):
            add_story.assert_called_with(
                comment.author, verb='VERB_COMMENTED_IMAGE',
                action_object=comment,
                target=comment.content_object)

    @patch("astrobin.models.UserProfile.get_scores")
    @patch("nested_comments.services.comment_notifications_service.push_notification")
    @patch("nested_comments.services.comment_notifications_service.add_story")
    def test_send_notifications_top_level(self, add_story, push_notification, get_scores):
        get_scores.return_value = {'user_scores_index': 2}

        image = Generators.image()
        commenter = Generators.user()

        comment = NestedCommentsGenerators.comment(author=commenter, target=image)

        push_notification.assert_called_with(mock.ANY, 'new_comment', mock.ANY)

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(mock.ANY, 'new_comment_reply', mock.ANY)

        add_story.assert_called_with(
            comment.author, verb='VERB_COMMENTED_IMAGE',
            action_object=comment,
            target=comment.content_object)

    @patch("astrobin.models.UserProfile.get_scores")
    @patch("nested_comments.services.comment_notifications_service.push_notification")
    @patch("nested_comments.services.comment_notifications_service.add_story")
    def test_send_notifications_reply(self, add_story, push_notification, get_scores):
        get_scores.return_value = {'user_scores_index': 2}

        image = Generators.image()
        commenter = Generators.user()
        commenter2 = Generators.user()

        comment = NestedCommentsGenerators.comment(author=commenter, target=image)

        push_notification.assert_called_with(mock.ANY, 'new_comment', mock.ANY)
        add_story.assert_called_with(
            comment.author, verb='VERB_COMMENTED_IMAGE',
            action_object=comment,
            target=comment.content_object)

        push_notification.reset_mock()
        add_story.resetMock()

        comment = NestedCommentsGenerators.comment(author=commenter2, target=image, parent=comment)

        calls = [
            mock.call(mock.ANY, 'new_comment', mock.ANY),
            mock.call(mock.ANY, 'new_comment_reply', mock.ANY),
        ]
        push_notification.assert_has_calls(calls, any_order=True)

        add_story.assert_called_with(
            comment.author, verb='VERB_COMMENTED_IMAGE',
            action_object=comment,
            target=comment.content_object)

    @patch("astrobin.models.UserProfile.get_scores")
    @patch("nested_comments.services.comment_notifications_service.push_notification")
    @patch("nested_comments.services.comment_notifications_service.add_story")
    def test_send_notifications_reply_to_image_owner(self, add_story, push_notification, get_scores):
        get_scores.return_value = {'user_scores_index': 2}

        image = Generators.image()
        commenter = Generators.user()

        comment = NestedCommentsGenerators.comment(author=image.user, target=image)

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(mock.ANY, 'new_comment', mock.ANY)

        add_story.assert_called_with(
            comment.author, verb='VERB_COMMENTED_IMAGE',
            action_object=comment,
            target=comment.content_object)

        push_notification.reset_mock()
        add_story.resetMock()

        comment = NestedCommentsGenerators.comment(author=commenter, target=image, parent=comment)

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(mock.ANY, 'new_comment', mock.ANY)

        calls = [
            mock.call(mock.ANY, 'new_comment_reply', mock.ANY),
        ]
        push_notification.assert_has_calls(calls, any_order=True)

        add_story.assert_called_with(
            comment.author, verb='VERB_COMMENTED_IMAGE',
            action_object=comment,
            target=comment.content_object)
