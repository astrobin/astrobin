from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from mock import patch

from astrobin.models import Image
from astrobin.tests.generators import Generators
from nested_comments.tests.nested_comments_generators import NestedCommentsGenerators


class CommentApprovalTest(TestCase):
    @patch("astrobin.models.UserProfile.get_scores")
    def test_mark_as_pending(self, get_scores):
        # Index:             NOT OK
        # Membership:        NOT OK
        # Approved comments: NOT OK

        get_scores.return_value = {'user_scores_index': 0}

        image = Generators.image()
        comment = NestedCommentsGenerators.comment(
            content_type=ContentType.objects.get_for_model(Image),
            oject_id=image.id,
        )

        self.assertTrue(comment.pending_moderation)

    @patch("astrobin.models.UserProfile.get_scores")
    def test_do_not_mark_as_pending_due_to_index(self, get_scores):
        # Index:                 OK
        # Membership:        NOT OK
        # Approved comments: NOT OK

        get_scores.return_value = {'user_scores_index': 10}

        image = Generators.image()
        comment = NestedCommentsGenerators.comment(
            content_type=ContentType.objects.get_for_model(Image),
            oject_id=image.id,
        )

        self.assertIsNone(comment.pending_moderation)

    @patch("astrobin.models.UserProfile.get_scores")
    def test_do_not_mark_as_pending_due_to_membership(self, get_scores):
        # Index:             NOT OK
        # Membership:            OK
        # Approved comments: NOT OK
        get_scores.return_value = {'user_scores_index': 0}

        image = Generators.image()
        author = Generators.user()
        Generators.premium_subscription(author, "AstroBin Premium 2020+")

        comment = NestedCommentsGenerators.comment(
            author=author,
            content_type=ContentType.objects.get_for_model(Image),
            oject_id=image.id,
        )

        self.assertIsNone(comment.pending_moderation)

    @patch("astrobin.models.UserProfile.get_scores")
    def test_mark_as_pending_due_to_insufficient_previously_approved_comments(self, get_scores):
        # Index:             NOT OK
        # Membership:        NOT OK
        # Approved comments: NOT OK

        get_scores.return_value = {'user_scores_index': 0}

        image = Generators.image()
        author = Generators.user()

        for i in range(0, 2):
            comment = NestedCommentsGenerators.comment(
                author=author,
                content_type=ContentType.objects.get_for_model(Image),
                oject_id=image.id,
            )
            comment.pending_moderation = None
            comment.save()

        comment = NestedCommentsGenerators.comment(
            author=author,
            content_type=ContentType.objects.get_for_model(Image),
            oject_id=image.id,
        )

        self.assertTrue(comment.pending_moderation)

    @patch("astrobin.models.UserProfile.get_scores")
    def test_mark_as_pending_due_to_insufficient_previously_approved_comments_with_one_pending(self, get_scores):
        # Index:             NOT OK
        # Membership:        NOT OK
        # Approved comments: NOT OK

        get_scores.return_value = {'user_scores_index': 0}

        image = Generators.image()
        author = Generators.user()

        for i in range(0, 2):
            comment = NestedCommentsGenerators.comment(
                author=author,
                content_type=ContentType.objects.get_for_model(Image),
                oject_id=image.id,
            )
            comment.pending_moderation = None
            comment.save()

        NestedCommentsGenerators.comment(
            author=author,
            content_type=ContentType.objects.get_for_model(Image),
            oject_id=image.id,
        )

        comment = NestedCommentsGenerators.comment(
            author=author,
            content_type=ContentType.objects.get_for_model(Image),
            oject_id=image.id,
        )

        self.assertTrue(comment.pending_moderation)

    @patch("astrobin.models.UserProfile.get_scores")
    def test_do_not_mark_as_pending_due_to_sufficient_previously_approved_comments(self, get_scores):
        # Index:             NOT OK
        # Membership:        NOT OK
        # Approved comments:     OK

        get_scores.return_value = {'user_scores_index': 0}

        image = Generators.image()
        author = Generators.user()

        for i in range(0, 3):
            comment = NestedCommentsGenerators.comment(
                author=author,
                content_type=ContentType.objects.get_for_model(Image),
                oject_id=image.id,
            )
            comment.pending_moderation = None
            comment.save()

        comment = NestedCommentsGenerators.comment(
            author=author,
            content_type=ContentType.objects.get_for_model(Image),
            oject_id=image.id,
        )

        self.assertIsNone(comment.pending_moderation)
