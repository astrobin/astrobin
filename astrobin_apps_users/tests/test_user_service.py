from datetime import datetime
from mock import patch

from django.test import TestCase

from astrobin.tests.generators import Generators
from astrobin_apps_users.services import UserService
from nested_comments.tests.nested_comments_generators import NestedCommentsGenerators
from toggleproperties.models import ToggleProperty


class TestUserService(TestCase):
    def test_get_all_images(self):
        user = Generators.user()
        image = Generators.image(user=user)
        wip = Generators.image(user=user, is_wip=True)
        corrupted = Generators.image(user=user, corrupted=True)
        deleted = Generators.image(user=user)

        deleted.delete()

        self.assertTrue(image in UserService(user).get_all_images())
        self.assertTrue(wip in UserService(user).get_all_images())
        self.assertTrue(corrupted in UserService(user).get_all_images())
        self.assertFalse(deleted in UserService(user).get_all_images())

    def test_get_corrupted_images(self):
        user = Generators.user()
        non_corrupted = Generators.image(user=user)
        corrupted = Generators.image(user=user, corrupted=True)

        self.assertFalse(non_corrupted in UserService(user).get_corrupted_images())
        self.assertTrue(corrupted in UserService(user).get_corrupted_images())

    def test_get_corrupted_images_when_final_revision_is_corrupted(self):
        user = Generators.user()
        image = Generators.image(user=user, is_final=False)
        Generators.imageRevision(image=image, is_final=True, corrupted=True)

        self.assertTrue(image in UserService(user).get_corrupted_images())

    def test_get_corrupted_images_when_non_final_revision_is_corrupted(self):
        user = Generators.user()
        image = Generators.image(user=user, is_final=False)
        Generators.imageRevision(image=image, is_final=False, corrupted=True)
        Generators.imageRevision(image=image, is_final=True, label='C')

        self.assertFalse(image in UserService(user).get_corrupted_images())

    def test_get_corrupted_images_when_non_final_revision_is_fine(self):
        user = Generators.user()
        image = Generators.image(user=user, is_final=True, corrupted=True)
        Generators.imageRevision(image=image, is_final=False)

        self.assertTrue(image in UserService(user).get_corrupted_images())

    def test_get_corrupted_images_when_corrupted_revision_is_deleted(self):
        user = Generators.user()
        image = Generators.image(user=user)
        revision = Generators.imageRevision(image=image, is_final=False, corrupted=True)

        revision.delete()

        self.assertFalse(image in UserService(user).get_corrupted_images())

    def test_get_corrupted_images_when_corrupted_revision_is_deleted_with_multiple(self):
        user = Generators.user()
        image = Generators.image(user=user)
        Generators.imageRevision(image=image, is_final=False)
        revision = Generators.imageRevision(image=image, is_final=False, corrupted=True, label='C')

        revision.delete()

        self.assertFalse(image in UserService(user).get_corrupted_images())

    def test_get_corrupted_images_when_multiple_corrupted_revisions(self):
        user = Generators.user()
        image = Generators.image(user=user, is_final=False, corrupted=True)
        Generators.imageRevision(image=image, is_final=False, corrupted=True, label='B')
        Generators.imageRevision(image=image, is_final=False, corrupted=True, label='C')
        Generators.imageRevision(image=image, is_final=True, corrupted=False, label='D')

        self.assertFalse(image in UserService(user).get_corrupted_images())

    def test_get_public_images(self):
        user = Generators.user()
        image = Generators.image(user=user)
        wip = Generators.image(user=user, is_wip=True)
        corrupted = Generators.image(user=user, corrupted=True)

        self.assertTrue(image in UserService(user).get_public_images())
        self.assertFalse(wip in UserService(user).get_public_images())
        self.assertTrue(corrupted in UserService(user).get_public_images())

    def test_get_wip_images(self):
        user = Generators.user()
        image = Generators.image(user=user)
        wip = Generators.image(user=user, is_wip=True)
        corrupted = Generators.image(user=user, corrupted=True)

        self.assertFalse(image in UserService(user).get_wip_images())
        self.assertTrue(wip in UserService(user).get_wip_images())
        self.assertFalse(corrupted in UserService(user).get_wip_images())

    def test_get_deleted_images(self):
        user = Generators.user()
        image = Generators.image(user=user)
        deleted = Generators.image(user=user)

        deleted.delete()

        self.assertFalse(image in UserService(user).get_deleted_images())
        self.assertTrue(deleted in UserService(user).get_deleted_images())

    def test_bookmarked_images(self):
        user1 = Generators.user()
        user2 = Generators.user()

        image = Generators.image(user=user1)
        corrupted = Generators.image(user=user1, corrupted=True)

        ToggleProperty.objects.create_toggleproperty("bookmark", image, user2)
        ToggleProperty.objects.create_toggleproperty("bookmark", corrupted, user2)

        bookmarked = UserService(user2).get_bookmarked_images()

        self.assertTrue(image in bookmarked)
        self.assertFalse(corrupted in bookmarked)

    def test_liked_images(self):
        user1 = Generators.user()
        user2 = Generators.user()

        image = Generators.image(user=user1)
        corrupted = Generators.image(user=user1, corrupted=True)

        ToggleProperty.objects.create_toggleproperty("like", image, user2)
        ToggleProperty.objects.create_toggleproperty("like", corrupted, user2)

        liked = UserService(user2).get_liked_images()

        self.assertTrue(image in liked)
        self.assertFalse(corrupted in liked)

    def test_get_image_numbers(self):
        user1 = Generators.user()
        user2 = Generators.user()

        Generators.image(user=user1)
        Generators.image(user=user1, is_wip=True)
        Generators.image(user=user1, corrupted=True)
        Generators.image(user=user1, corrupted=True, recovered=datetime.now())

        image2 = Generators.image(user=user2)
        ToggleProperty.objects.create_toggleproperty("bookmark", image2, user1)
        ToggleProperty.objects.create_toggleproperty("like", image2, user1)

        image_numbers = UserService(user1).get_image_numbers()

        self.assertEquals(image_numbers['public_images_no'], 3)
        self.assertEquals(image_numbers['wip_images_no'], 1)
        self.assertEquals(image_numbers['corrupted_no'], 2)
        self.assertEquals(image_numbers['recovered_no'], 1)

    def test_get_image_numbers_not_including_corrupted(self):
        user1 = Generators.user()
        user2 = Generators.user()

        Generators.image(user=user1)
        Generators.image(user=user1, is_wip=True)
        Generators.image(user=user1, corrupted=True)

        image2 = Generators.image(user=user2)
        ToggleProperty.objects.create_toggleproperty("bookmark", image2, user1)
        ToggleProperty.objects.create_toggleproperty("like", image2, user1)

        image_numbers = UserService(user1).get_image_numbers(include_corrupted=False)

        self.assertEquals(image_numbers['public_images_no'], 1)
        self.assertEquals(image_numbers['wip_images_no'], 1)
        self.assertEquals(image_numbers['corrupted_no'], 1)

    def test_can_like_image_superuser(self):
        user = Generators.user()
        image = Generators.image()
        user.is_superuser = True
        user.save()

        self.assertTrue(UserService(user).can_like(image))

    @patch('django.contrib.auth.models.User.is_authenticated')
    def test_can_like_image_anon(self, is_authenticated):
        user = Generators.user()
        image = Generators.image()

        is_authenticated.return_value = False

        self.assertFalse(UserService(user).can_like(image))

    @patch('astrobin_apps_premium.templatetags.astrobin_apps_premium_tags.is_free')
    @patch('astrobin.models.UserProfile.get_scores')
    def test_can_like_image_index_too_low(self, get_scores, is_free):
        user = Generators.user()
        image = Generators.image()

        is_free.return_value = True
        get_scores.return_value = {'user_scores_index': .5}

        self.assertFalse(UserService(user).can_like(image))

    @patch('astrobin_apps_premium.templatetags.astrobin_apps_premium_tags.is_free')
    @patch('astrobin.models.UserProfile.get_scores')
    def test_can_like_image_same_user(self, get_scores, is_free):
        user = Generators.user()
        image = Generators.image(user=user)

        is_free.return_value = False
        get_scores.return_value = {'user_scores_index': 2}

        self.assertFalse(UserService(user).can_like(image))

    @patch('astrobin_apps_premium.templatetags.astrobin_apps_premium_tags.is_free')
    @patch('astrobin.models.UserProfile.get_scores')
    def test_can_like_image_ok(self, get_scores,  is_free):
        user = Generators.user()
        image = Generators.image()

        is_free.return_value = False
        get_scores.return_value = {'user_scores_index': 2}

        self.assertTrue(UserService(user).can_like(image))

    @patch('astrobin_apps_premium.templatetags.astrobin_apps_premium_tags.is_free')
    @patch('astrobin.models.UserProfile.get_scores')
    def test_can_like_comment_same_user(self, get_scores, is_free):
        user = Generators.user()
        comment = NestedCommentsGenerators.comment(author=user)

        is_free.return_value = False
        get_scores.return_value = {'user_scores_index': 2}

        self.assertFalse(UserService(user).can_like(comment))

    @patch('astrobin_apps_premium.templatetags.astrobin_apps_premium_tags.is_free')
    @patch('astrobin.models.UserProfile.get_scores')
    def test_can_like_comment_ok(self, get_scores, is_free):
        user = Generators.user()
        comment = NestedCommentsGenerators.comment()

        is_free.return_value = False
        get_scores.return_value = {'user_scores_index': 2}

        self.assertTrue(UserService(user).can_like(comment))

    @patch('astrobin_apps_premium.templatetags.astrobin_apps_premium_tags.is_free')
    @patch('astrobin.models.UserProfile.get_scores')
    def test_can_like_comment_same_user(self, get_scores, is_free):
        user = Generators.user()
        comment = NestedCommentsGenerators.comment(author=user)

        is_free.return_value = False
        get_scores.return_value = {'user_scores_index': 2}

        self.assertFalse(UserService(user).can_like(comment))

    @patch('astrobin_apps_premium.templatetags.astrobin_apps_premium_tags.is_free')
    @patch('astrobin.models.UserProfile.get_scores')
    def test_can_like_post_ok(self, get_scores, is_free):
        user = Generators.user()
        post = Generators.forum_post()

        is_free.return_value = False
        get_scores.return_value = {'user_scores_index': 2}

        self.assertTrue(UserService(user).can_like(post))

    @patch('astrobin_apps_premium.templatetags.astrobin_apps_premium_tags.is_free')
    @patch('astrobin.models.UserProfile.get_scores')
    def test_can_like_post_same_user(self, get_scores, is_free):
        user = Generators.user()
        post = Generators.forum_post(user=user)

        is_free.return_value = False
        get_scores.return_value = {'user_scores_index': 2}

        self.assertFalse(UserService(user).can_like(post))
