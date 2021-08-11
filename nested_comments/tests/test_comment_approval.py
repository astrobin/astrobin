from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from mock import patch
from notification.models import NoticeType, NoticeSetting
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from astrobin.models import Image
from astrobin.tests.generators import Generators
from nested_comments.models import NestedComment
from nested_comments.tests.nested_comments_generators import NestedCommentsGenerators


class CommentApprovalTest(TestCase):
    def setUp(self) -> None:
        NoticeType.objects.create(
            label='new_image_comment_moderation',
            display='',
            description='',
            default=2)

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

    def test_approval_api_login_required(self):
        client = APIClient()

        image = Generators.image()
        comment = NestedCommentsGenerators.comment(target=image, pending_moderation=True)

        response = client.post(reverse('nested_comments:nestedcomments-approve', args=(comment.pk,)))
        self.assertEqual(401, response.status_code)

    def test_approval_api_not_owner(self):
        client = APIClient()

        image = Generators.image()
        comment = NestedCommentsGenerators.comment(target=image, pending_moderation=True)

        client.force_authenticate(user=comment.author)

        response = client.post(reverse('nested_comments:nestedcomments-approve', args=(comment.pk,)))
        self.assertEqual(403, response.status_code)

    def test_approval_api_not_pending_moderation(self):
        client = APIClient()

        image = Generators.image()
        comment = NestedCommentsGenerators.comment(target=image, pending_moderation=False)

        client.force_authenticate(user=image.user)

        response = client.post(reverse('nested_comments:nestedcomments-approve', args=(comment.pk,)))
        self.assertEqual(400, response.status_code)

    def test_approval_api_all_ok(self):
        client = APIClient()

        image = Generators.image()
        comment = NestedCommentsGenerators.comment(target=image, pending_moderation=True)

        client.force_authenticate(user=image.user)

        response = client.post(reverse('nested_comments:nestedcomments-approve', args=(comment.pk,)))
        self.assertEqual(200, response.status_code)

        comment = NestedComment.objects.get(pk=comment.pk)

        self.assertFalse(comment.pending_moderation)
        self.assertEqual(image.user, comment.moderator)

    def test_rejection_api_login_required(self):
        client = APIClient()

        image = Generators.image()
        comment = NestedCommentsGenerators.comment(target=image, pending_moderation=True)

        response = client.post(reverse('nested_comments:nestedcomments-reject', args=(comment.pk,)))
        self.assertEqual(401, response.status_code)

    def test_rejection_api_not_owner(self):
        client = APIClient()

        image = Generators.image()
        comment = NestedCommentsGenerators.comment(target=image, pending_moderation=True)

        client.force_authenticate(user=comment.author)

        response = client.post(reverse('nested_comments:nestedcomments-reject', args=(comment.pk,)))
        self.assertEqual(403, response.status_code)

    def test_rejection_api_not_pending_moderation(self):
        client = APIClient()

        image = Generators.image()
        comment = NestedCommentsGenerators.comment(target=image, pending_moderation=False)

        client.force_authenticate(user=image.user)

        response = client.post(reverse('nested_comments:nestedcomments-reject', args=(comment.pk,)))
        self.assertEqual(400, response.status_code)

    def test_rejection_api_all_ok(self):
        client = APIClient()

        image = Generators.image()
        comment = NestedCommentsGenerators.comment(target=image, pending_moderation=True)

        client.force_authenticate(user=image.user)

        response = client.post(reverse('nested_comments:nestedcomments-reject', args=(comment.pk,)))
        self.assertEqual(200, response.status_code)

        comment = NestedComment.objects.get(pk=comment.pk)

        self.assertFalse(comment.pending_moderation)
        self.assertEqual(image.user, comment.moderator)
        self.assertTrue(comment.deleted)
