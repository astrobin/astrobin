import time

from django.test import TestCase

from astrobin.models import Image
from astrobin.tests.generators import Generators
from astrobin_apps_images.services import CollectionService


class TestCollectionService(TestCase):
    def test_add_remove_images(self):
        collection = Generators.collection()

        image1 = Generators.image(user=collection.user)
        image2 = Generators.image(user=collection.user)
        image3 = Generators.image(user=collection.user)
        image4 = Generators.image(user=collection.user)
        image5 = Generators.image(user=collection.user)

        CollectionService(collection).add_remove_images(
            Image.objects.filter(pk__in=[
                image1.pk, image2.pk, image3.pk, image4.pk, image5.pk
            ])
        )

        self.assertTrue(image1 in collection.images.all())
        self.assertTrue(image2 in collection.images.all())
        self.assertTrue(image3 in collection.images.all())
        self.assertTrue(image4 in collection.images.all())
        self.assertTrue(image5 in collection.images.all())

        image1.refresh_from_db()
        image2.refresh_from_db()
        image3.refresh_from_db()
        image4.refresh_from_db()
        image5.refresh_from_db()

        updated1 = image1.updated
        updated2 = image2.updated
        updated3 = image3.updated
        updated4 = image4.updated
        updated5 = image5.updated

        time.sleep(.1)

        CollectionService(collection).add_remove_images(
            Image.objects.filter(
                pk__in=[
                    image1.pk, image2.pk, image4.pk, image5.pk
                ]
            )
        )

        image2.refresh_from_db()
        image3.refresh_from_db()
        image4.refresh_from_db()
        image5.refresh_from_db()

        self.assertTrue(image1 in collection.images.all())
        self.assertTrue(image2 in collection.images.all())
        self.assertFalse(image3 in collection.images.all())
        self.assertTrue(image4 in collection.images.all())
        self.assertTrue(image5 in collection.images.all())

        # Only image3 should've been updated, because the other four have not been added nor removed.
        self.assertEqual(image1.updated, updated1)
        self.assertEqual(image2.updated, updated2)
        self.assertGreater(image3.updated, updated3)
        self.assertEqual(image4.updated, updated4)
        self.assertEqual(image5.updated, updated5)

    def test_add_images(self):
        collection = Generators.collection()

        image1 = Generators.image(user=collection.user)
        image2 = Generators.image(user=collection.user)

        updated1 = image1.updated
        updated2 = image2.updated

        time.sleep(.1)

        CollectionService(collection).add_remove_images(
            Image.objects.filter(pk__in=[image1.pk, image2.pk])
        )

        image1.refresh_from_db()
        image2.refresh_from_db()

        self.assertTrue(image1 in collection.images.all())
        self.assertTrue(image2 in collection.images.all())

        self.assertTrue(image1.updated > updated1)
        self.assertTrue(image2.updated > updated2)

    def test_remove_images(self):
        collection = Generators.collection()

        image1 = Generators.image(user=collection.user)
        image2 = Generators.image(user=collection.user)
        image3 = Generators.image(user=collection.user)
        image4 = Generators.image(user=collection.user)

        CollectionService(collection).add_remove_images(
            Image.objects.filter(pk__in=[image1.pk, image2.pk, image3.pk, image4.pk])
        )

        # Store the 'updated' value after it's been changed due to adding.
        image3.refresh_from_db()
        image4.refresh_from_db()
        updated3 = image3.updated
        updated4 = image4.updated

        time.sleep(.1)

        CollectionService(collection).add_remove_images(
            Image.objects.filter(pk__in=[image1.pk, image2.pk])
        )

        image3.refresh_from_db()
        image4.refresh_from_db()

        self.assertFalse(image3 in collection.images.all())
        self.assertFalse(image4 in collection.images.all())

        self.assertTrue(image3.updated > updated3)
        self.assertTrue(image4.updated > updated4)
