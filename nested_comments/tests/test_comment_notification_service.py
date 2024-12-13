import mock
from django.test import TestCase
from mock import patch
from notification.models import NoticeType, NoticeSetting

from astrobin.stories import ACTSTREAM_VERB_COMMENTED_IMAGE
from astrobin.tests.generators import Generators
from nested_comments.services import CommentNotificationsService
from nested_comments.tests.nested_comments_generators import NestedCommentsGenerators


class CommentNotificationServiceTest(TestCase):
    @patch("astrobin.models.UserProfile.get_scores")
    @patch("nested_comments.services.comment_notifications_service.push_notification")
    @patch("nested_comments.services.comment_notifications_service.add_story")
    def test_send_notifications_pending_moderation(self, add_story, push_notification, get_scores):
        get_scores.return_value = {'user_scores_index': .5}
        comment = NestedCommentsGenerators.comment()

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(mock.ANY, mock.ANY, 'new_comment', mock.ANY)

        with self.assertRaises(AssertionError):
            add_story.assert_called_with(
                comment.author, verb=ACTSTREAM_VERB_COMMENTED_IMAGE,
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
            push_notification.assert_called_with(mock.ANY, comment.author, 'new_comment', mock.ANY)

        with self.assertRaises(AssertionError):
            add_story.assert_called_with(
                comment.author, verb=ACTSTREAM_VERB_COMMENTED_IMAGE,
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

        push_notification.assert_called_with(mock.ANY, commenter, 'new_comment', mock.ANY)

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(mock.ANY, commenter, 'new_comment_reply', mock.ANY)

        with self.assertRaises(AssertionError):
            add_story.assert_called_with(
                comment.author, verb=ACTSTREAM_VERB_COMMENTED_IMAGE,
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

        push_notification.assert_called_with(mock.ANY, commenter, 'new_comment', mock.ANY)

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(mock.ANY, commenter, 'new_comment_reply', mock.ANY)

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(mock.ANY, commenter, 'new_comment_mention', mock.ANY)

        add_story.assert_called_with(
            comment.author,
            verb=ACTSTREAM_VERB_COMMENTED_IMAGE,
            action_object=comment,
            target=comment.content_object,
            like_count=0,
            bookmark_count=0,
            comment_count=1,
            comment_html=mock.ANY
        )

    @patch("astrobin.models.UserProfile.get_scores")
    @patch("nested_comments.services.comment_notifications_service.push_notification")
    @patch("nested_comments.services.comment_notifications_service.add_story")
    def test_send_notifications_top_level_with_mention_but_no_notification(
            self, add_story, push_notification, get_scores):
        get_scores.return_value = {'user_scores_index': 2}

        image = Generators.image()
        commenter = Generators.user()

        comment = NestedCommentsGenerators.comment(
            author=commenter, target=image, text='[quote="%s"]Foo[/quote]' % image.user.username)

        push_notification.assert_has_calls([
            mock.call(mock.ANY, commenter, 'new_comment', mock.ANY),
            mock.call(mock.ANY, commenter, 'new_comment_mention', mock.ANY),
        ], any_order=True)

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(mock.ANY, commenter, 'new_comment_reply', mock.ANY)

        add_story.assert_called_with(
            comment.author,
            verb=ACTSTREAM_VERB_COMMENTED_IMAGE,
            action_object=comment,
            target=comment.content_object,
            like_count=0,
            bookmark_count=0,
            comment_count=1,
            comment_html=mock.ANY
        )

    @patch("astrobin.models.UserProfile.get_scores")
    @patch("nested_comments.services.comment_notifications_service.push_notification")
    @patch("nested_comments.services.comment_notifications_service.add_story")
    def test_send_notifications_top_level_with_mention_and_notification(
            self, add_story, push_notification, get_scores):
        get_scores.return_value = {'user_scores_index': 2}

        image = Generators.image()
        commenter = Generators.user()
        NoticeSetting.for_user(image.user, NoticeType.objects.get(label='new_comment_mention'), 1)

        comment = NestedCommentsGenerators.comment(
            author=commenter, target=image, text='[quote="%s"]Foo[/quote]' % image.user.username)

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(mock.ANY, commenter, 'new_comment', mock.ANY)

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(mock.ANY, commenter, 'new_comment_reply', mock.ANY)

        push_notification.assert_called_with([image.user], commenter, 'new_comment_mention', mock.ANY)

        add_story.assert_called_with(
            comment.author,
            verb=ACTSTREAM_VERB_COMMENTED_IMAGE,
            action_object=comment,
            target=comment.content_object,
            like_count=0,
            bookmark_count=0,
            comment_count=1,
            comment_html=mock.ANY
        )

    @patch("astrobin.models.UserProfile.get_scores")
    @patch("nested_comments.services.comment_notifications_service.push_notification")
    @patch("nested_comments.services.comment_notifications_service.add_story")
    def test_send_notifications_reply(self, add_story, push_notification, get_scores):
        get_scores.return_value = {'user_scores_index': 2}

        image = Generators.image()
        commenter = Generators.user()
        replier = Generators.user()

        comment = NestedCommentsGenerators.comment(author=commenter, target=image)

        push_notification.assert_called_with(mock.ANY, commenter, 'new_comment', mock.ANY)
        add_story.assert_called_with(
            comment.author,
            verb=ACTSTREAM_VERB_COMMENTED_IMAGE,
            action_object=comment,
            target=comment.content_object,
            like_count=0,
            bookmark_count=0,
            comment_count=1,
            comment_html=mock.ANY
        )

        push_notification.reset_mock()
        add_story.resetMock()

        comment = NestedCommentsGenerators.comment(author=replier, target=image, parent=comment)

        push_notification.assert_has_calls([
            mock.call(mock.ANY, replier, 'new_comment', mock.ANY),
            mock.call(mock.ANY, replier, 'new_comment_reply', mock.ANY),
        ], any_order=True)

        add_story.assert_called_with(
            comment.author,
            verb=ACTSTREAM_VERB_COMMENTED_IMAGE,
            action_object=comment,
            target=comment.content_object,
            like_count=0,
            bookmark_count=0,
            comment_count=2,
            comment_html=mock.ANY
        )

    @patch("astrobin.models.UserProfile.get_scores")
    @patch("nested_comments.services.comment_notifications_service.push_notification")
    @patch("nested_comments.services.comment_notifications_service.add_story")
    def test_send_notifications_reply_with_mention_but_no_notification(
            self, add_story, push_notification, get_scores):
        get_scores.return_value = {'user_scores_index': 2}

        image = Generators.image()
        commenter = Generators.user()
        replier = Generators.user()

        comment = NestedCommentsGenerators.comment(author=commenter, target=image)

        push_notification.assert_called_with([image.user], commenter, 'new_comment', mock.ANY)
        add_story.assert_called_with(
            comment.author,
            verb=ACTSTREAM_VERB_COMMENTED_IMAGE,
            action_object=comment,
            target=comment.content_object,
            like_count=0,
            bookmark_count=0,
            comment_count=1,
            comment_html=mock.ANY
        )

        push_notification.reset_mock()
        add_story.resetMock()

        comment = NestedCommentsGenerators.comment(
            author=replier, target=image, parent=comment, text='[quote="%s"]Foo[/quote]' % commenter.username)

        push_notification.assert_has_calls([
            mock.call([image.user], replier, 'new_comment', mock.ANY),
            mock.call([commenter], replier, 'new_comment_reply', mock.ANY),
        ], any_order=True)

        # This is called anyway but will have no effect since there is not NoticeSetting for this user. The goal of this
        # test is to check that the 'new_comment' notification is sent.
        push_notification.assert_called_with([commenter], replier, 'new_comment_mention', mock.ANY)

        add_story.assert_called_with(
            comment.author,
            verb=ACTSTREAM_VERB_COMMENTED_IMAGE,
            action_object=comment,
            target=comment.content_object,
            like_count=0,
            bookmark_count=0,
            comment_count=2,
            comment_html=mock.ANY
        )

    @patch("astrobin.models.UserProfile.get_scores")
    @patch("nested_comments.services.comment_notifications_service.push_notification")
    @patch("nested_comments.services.comment_notifications_service.add_story")
    def test_send_notifications_reply_with_mention_and_notification(
            self, add_story, push_notification, get_scores):
        get_scores.return_value = {'user_scores_index': 2}

        image = Generators.image()
        commenter = Generators.user()
        replier = Generators.user()
        NoticeSetting.for_user(commenter, NoticeType.objects.get(label='new_comment_mention'), 1)

        comment = NestedCommentsGenerators.comment(author=commenter, target=image)

        push_notification.assert_called_with([image.user], commenter, 'new_comment', mock.ANY)
        add_story.assert_called_with(
            comment.author, verb=ACTSTREAM_VERB_COMMENTED_IMAGE,
            action_object=comment,
            target=comment.content_object,
            like_count=0,
            bookmark_count=0,
            comment_count=1,
            comment_html=mock.ANY
        )

        push_notification.reset_mock()
        add_story.resetMock()

        comment = NestedCommentsGenerators.comment(
            author=replier, target=image, parent=comment, text='[quote="%s"]Foo[/quote]' % commenter.username)

        push_notification.assert_has_calls([
            mock.call([image.user], replier, 'new_comment', mock.ANY),
        ], any_order=True)

        push_notification.assert_called_with([commenter], replier, 'new_comment_mention', mock.ANY)

        add_story.assert_called_with(
            comment.author,
            verb=ACTSTREAM_VERB_COMMENTED_IMAGE,
            action_object=comment,
            target=comment.content_object,
            like_count=0,
            bookmark_count=0,
            comment_count=2,
            comment_html=mock.ANY
        )

    @patch("astrobin.models.UserProfile.get_scores")
    @patch("nested_comments.services.comment_notifications_service.push_notification")
    @patch("nested_comments.services.comment_notifications_service.add_story")
    def test_send_notifications_reply_to_image_owner(self, add_story, push_notification, get_scores):
        get_scores.return_value = {'user_scores_index': 2}

        image = Generators.image()
        commenter = Generators.user()

        comment = NestedCommentsGenerators.comment(author=image.user, target=image)

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(mock.ANY, commenter, 'new_comment', mock.ANY)

        add_story.assert_called_with(
            comment.author,
            verb=ACTSTREAM_VERB_COMMENTED_IMAGE,
            action_object=comment,
            target=comment.content_object,
            like_count=0,
            bookmark_count=0,
            comment_count=1,
            comment_html=mock.ANY
        )

        push_notification.reset_mock()
        add_story.resetMock()

        comment = NestedCommentsGenerators.comment(author=commenter, target=image, parent=comment)

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(mock.ANY, comment.author, 'new_comment', mock.ANY)

        calls = [
            mock.call(mock.ANY, commenter, 'new_comment_reply', mock.ANY),
        ]
        push_notification.assert_has_calls(calls, any_order=True)

        add_story.assert_called_with(
            comment.author,
            verb=ACTSTREAM_VERB_COMMENTED_IMAGE,
            action_object=comment,
            target=comment.content_object,
            like_count=0,
            bookmark_count=0,
            comment_count=2,
            comment_html=mock.ANY
        )

    @patch("astrobin.models.UserProfile.get_scores")
    @patch("nested_comments.services.comment_notifications_service.push_notification")
    @patch("nested_comments.services.comment_notifications_service.add_story")
    def test_send_notifications_reply_to_image_owner_with_mention_but_no_notification(
            self, add_story, push_notification, get_scores):
        get_scores.return_value = {'user_scores_index': 2}

        image = Generators.image()
        commenter = Generators.user()

        comment = NestedCommentsGenerators.comment(author=image.user, target=image)

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(mock.ANY, commenter, 'new_comment', mock.ANY)

        add_story.assert_called_with(
            comment.author,
            verb=ACTSTREAM_VERB_COMMENTED_IMAGE,
            action_object=comment,
            target=comment.content_object,
            like_count=0,
            bookmark_count=0,
            comment_count=1,
            comment_html=mock.ANY
        )

        push_notification.reset_mock()
        add_story.resetMock()

        comment = NestedCommentsGenerators.comment(
            author=commenter, target=image, parent=comment, text='[quote="%s"]Foo[/quote]' % image.user)

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(mock.ANY, comment.author, 'new_comment', mock.ANY)

        calls = [
            mock.call(mock.ANY, commenter, 'new_comment_reply', mock.ANY),
        ]
        push_notification.assert_has_calls(calls, any_order=True)

        # This is called anyway but will have no effect since there is not NoticeSetting for this user. The goal of this
        # test is to check that the 'new_comment' notification is sent.
        push_notification.assert_called_with([image.user], commenter, 'new_comment_mention', mock.ANY)

        add_story.assert_called_with(
            comment.author,
            verb=ACTSTREAM_VERB_COMMENTED_IMAGE,
            action_object=comment,
            target=comment.content_object,
            like_count=0,
            bookmark_count=0,
            comment_count=2,
            comment_html=mock.ANY
        )

    @patch("astrobin.models.UserProfile.get_scores")
    @patch("nested_comments.services.comment_notifications_service.push_notification")
    @patch("nested_comments.services.comment_notifications_service.add_story")
    def test_send_notifications_reply_to_image_owner_with_mention_and_notification(
            self, add_story, push_notification, get_scores):
        get_scores.return_value = {'user_scores_index': 2}

        image = Generators.image()
        commenter = Generators.user()
        NoticeSetting.for_user(image.user, NoticeType.objects.get(label='new_comment_mention'), 1)

        comment = NestedCommentsGenerators.comment(author=image.user, target=image)

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(mock.ANY, commenter, 'new_comment', mock.ANY)

        add_story.assert_called_with(
            comment.author,
            verb=ACTSTREAM_VERB_COMMENTED_IMAGE,
            action_object=comment,
            target=comment.content_object,
            like_count=0,
            bookmark_count=0,
            comment_count=1,
            comment_html=mock.ANY
        )

        push_notification.reset_mock()
        add_story.resetMock()

        comment = NestedCommentsGenerators.comment(
            author=commenter, target=image, parent=comment, text='[quote="%s"]Foo[/quote]' % image.user)

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with([image.user], comment.author, 'new_comment', mock.ANY)

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with([image.user], comment.author, 'new_comment_reply', mock.ANY)

        push_notification.assert_called_with([image.user], commenter, 'new_comment_mention', mock.ANY)

        add_story.assert_called_with(
            comment.author,
            verb=ACTSTREAM_VERB_COMMENTED_IMAGE,
            action_object=comment,
            target=comment.content_object,
            like_count=0,
            bookmark_count=0,
            comment_count=2,
            comment_html=mock.ANY
        )

    @patch("nested_comments.services.comment_notifications_service.push_notification")
    def test_send_moderation_required_notification_non_pending_moderation(self, push_notification):
        image = Generators.image()
        comment = NestedCommentsGenerators.comment(target=image)

        push_notification.reset_mock()

        CommentNotificationsService(comment).send_moderation_required_notification()

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with([image.user], None, 'new_image_comment_moderation', mock.ANY)

    @patch("nested_comments.services.comment_notifications_service.push_notification")
    def test_send_moderation_required_notification_non_image_target(self, push_notification):
        post = Generators.forum_post()
        comment = NestedCommentsGenerators.comment(target=post, pending_moderation=True)

        push_notification.reset_mock()

        CommentNotificationsService(comment).send_moderation_required_notification()

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with([post.user], None, 'new_image_comment_moderation', mock.ANY)

    @patch("nested_comments.services.comment_notifications_service.push_notification")
    def test_send_moderation_required_notification_send_notification(self, push_notification):
        image = Generators.image()
        comment = NestedCommentsGenerators.comment(target=image, pending_moderation=True)

        push_notification.reset_mock()

        CommentNotificationsService(comment).send_moderation_required_notification()

        push_notification.assert_called_with([image.user], None, 'new_image_comment_moderation', mock.ANY)
