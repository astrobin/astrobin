from django.test import TestCase

from astrobin.tests.generators import Generators
from astrobin_apps_users.services import UserService
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

    def test_get_public_images(self):
        user = Generators.user()
        image = Generators.image(user=user)
        wip = Generators.image(user=user, is_wip=True)
        corrupted = Generators.image(user=user, corrupted=True)

        self.assertTrue(image in UserService(user).get_public_images())
        self.assertFalse(wip in UserService(user).get_public_images())
        self.assertFalse(corrupted in UserService(user).get_public_images())

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

        image2 = Generators.image(user=user2)
        ToggleProperty.objects.create_toggleproperty("bookmark", image2, user1)
        ToggleProperty.objects.create_toggleproperty("like", image2, user1)

        image_numbers = UserService(user1).get_image_numbers()

        self.assertEquals(image_numbers['public_images_no'], 1)
        self.assertEquals(image_numbers['wip_images_no'], 1)
        self.assertEquals(image_numbers['corrupted_no'], 1)
        self.assertEquals(image_numbers['bookmarked_no'], 1)
        self.assertEquals(image_numbers['liked_no'], 1)
