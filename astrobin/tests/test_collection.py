import json
import re

import simplejson
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from astrobin.enums.moderator_decision import ModeratorDecision
from astrobin.models import Collection, Image
from astrobin.tests.generators import Generators


class CollectionTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test', 'test@test.com', 'password')
        self.user2 = User.objects.create_user('test2', 'test@test.com', 'password')

        self.user.default_gallery_section = 5
        self.user.save()

    ###########################################################################
    # HELPERS                                                                 #
    ###########################################################################

    def _do_upload(self, filename, wip=False):
        data = {'image_file': open(filename, 'rb')}
        if wip:
            data['wip'] = True

        return self.client.post(
            reverse('image_upload_process'),
            data,
            follow=True)

    def _get_last_image(self):
        return Image.objects_including_wip.all().order_by('-id')[0]

    def _create_collection(self, user, name, description):
        return self.client.post(
            reverse('user_collections_create', args=(user.username,)),
            {
                'name': name,
                'description': description,
            },
            follow=True
        )

    def _get_last_collection(self):
        return Collection.objects.all().order_by('-id')[0]

    ###########################################################################
    # View tests                                                              #
    ###########################################################################

    def test_collections_list_view(self):
        # Anon user, no collections
        response = self.client.get(reverse('user_collections_list', args=(self.user.username,)))
        self.assertContains(response, "This user does not have any collections")

        # Other user, no collections
        self.client.login(username='test2', password='password')
        response = self.client.get(reverse('user_collections_list', args=(self.user.username,)))
        self.assertContains(response, "This user does not have any collections")
        self.client.logout()

        # Owner, no collection
        self.client.login(username='test', password='password')
        response = self.client.get(reverse('user_collections_list', args=(self.user.username,)))
        self.assertContains(response, "You do not have any collections")
        self.client.logout()

        # Create a collection
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        response = self._create_collection(self.user, 'test_collection', 'test_description')

        image = self._get_last_image()
        collection = self._get_last_collection()
        self.assertEqual(collection.name, 'test_collection')
        self.assertEqual(collection.description, 'test_description')
        response = self.client.get(reverse('user_collections_list', args=(self.user.username,)))
        self.assertContains(response, "test_collection")

        # Collection has no images
        self.assertContains(response, "collection-image empty")

    def test_collection_update_view(self):
        self.client.login(username='test', password='password')
        self._create_collection(self.user, 'test_collection', 'test_description')
        collection = self._get_last_collection()

        self._do_upload('astrobin/fixtures/test.jpg')
        image1 = self._get_last_image()
        self._do_upload('astrobin/fixtures/test.jpg')
        image2 = self._get_last_image()

        collection.images.add(image1)
        collection.images.add(image2)

        # Test that image2 is the cover (latest uploaded)
        response = self.client.get(
            reverse('user_collections_list', args=(self.user.username,))
        )
        self.assertIsNotNone(
            re.search(
                r'data-id="%d"\s+data-id-or-hash="%s"\s+data-alias="%s"' % (image2.pk, image2.get_id(), "collection"),
                response.content.decode('utf-8')
            )
        )

        response = self.client.post(
            reverse('user_collections_update', args=(self.user.username, collection.pk)),
            {
                'name': 'edited_name',
                'description': 'edited_description',
                'cover': image1.pk,
            },
            follow=True
        )
        self.assertContains(response, "edited_name")

        response = self.client.get(
            reverse('user_collections_list', args=(self.user.username,))
        )
        self.assertIsNotNone(
            re.search(
                r'data-id="%d"\s+data-id-or-hash="%s"\s+data-alias="%s"' % (image1.pk, image1.get_id(), "collection"),
                response.content.decode('utf-8')
            )
        )

    def test_collection_delete_view(self):
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        self._create_collection(self.user, 'test_collection', 'test_description')
        collection = self._get_last_collection()
        response = self.client.post(
            reverse('user_collections_delete', args=(self.user.username, collection.pk)),
            follow=True)
        self.assertNotContains(response, "test_collection")

    def test_collection_add_remove_images_view(self):
        # Create a collection
        self.client.login(username='test', password='password')
        self._create_collection(self.user, 'test_collection', 'test_description')
        collection = self._get_last_collection()
        self._do_upload('astrobin/fixtures/test.jpg')
        image = self._get_last_image()
        self._do_upload('astrobin/fixtures/test.jpg')
        image2 = self._get_last_image()

        response = self.client.get(
            reverse('user_collections_add_remove_images', args=(self.user.username, collection.pk)),
        )
        self.assertEqual(response.status_code, 200)

        self.client.post(
            reverse('user_collections_add_remove_images', args=(self.user.username, collection.pk)),
            {
                'images[]': [image.pk, image2.pk],
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True)

        self.assertEqual(collection.images.count(), 2)

    def test_collection_order_by_tag(self):
        self.client.login(username='test', password='password')
        self._create_collection(self.user, 'test_collection', 'test_description')

        self._do_upload('astrobin/fixtures/test.jpg')
        image1 = self._get_last_image()
        Generators.key_value_tag(image=image1, key="a", value=1)
        Generators.key_value_tag(image=image1, key="b", value=2)

        self._do_upload('astrobin/fixtures/test.jpg')
        image2 = self._get_last_image()
        Generators.key_value_tag(image=image2, key="a", value=2)
        Generators.key_value_tag(image=image2, key="b", value=1)

        collection = Collection.objects.create(user=self.user, order_by_tag="a")
        collection.images.add(image1, image2)

        response = self.client.get(reverse('user_collections_detail', args=(self.user.username, collection.pk,)))

        self.assertContains(response, image1.hash)
        self.assertContains(response, image2.hash)
        encoded_response = response.content.decode('utf-8')
        self.assertTrue(encoded_response.find(image1.hash) < encoded_response.find(image2.hash))

        collection.order_by_tag = "b"
        collection.save()

        response = self.client.get(reverse('user_collections_detail', args=(self.user.username, collection.pk,)))

        self.assertContains(response, image1.hash)
        self.assertContains(response, image2.hash)
        encoded_response = response.content.decode('utf-8')
        self.assertTrue(encoded_response.find(image2.hash) < encoded_response.find(image1.hash))

        image2.keyvaluetags.filter(key="b").delete()

        response = self.client.get(reverse('user_collections_detail', args=(self.user.username, collection.pk,)))
        encoded_response = response.content.decode('utf-8')

        self.assertContains(response, image1.hash)
        self.assertContains(response, image2.hash)
        self.assertTrue(encoded_response.find(image1.hash) < encoded_response.find(image2.hash))

    def test_collection_quick_edit_key_value_tags(self):
        self.client.login(username='test', password='password')
        self._create_collection(self.user, 'test_collection', 'test_description')

        self._do_upload('astrobin/fixtures/test.jpg')
        image1 = self._get_last_image()
        Generators.key_value_tag(image=image1, key="a", value=1)

        self._do_upload('astrobin/fixtures/test.jpg')
        image2 = self._get_last_image()
        Generators.key_value_tag(image=image2, key="a", value=2)

        collection = Collection.objects.create(user=self.user, order_by_tag="a")
        collection.images.add(image1, image2)

        response = self.client.get(
            reverse('user_collections_quick_edit_key_value_tags', args=(self.user.username, collection.pk,)))

        self.assertContains(response, "a=1")
        self.assertContains(response, "a=2")

        response = self.client.post(
            reverse('user_collections_quick_edit_key_value_tags', args=(self.user.username, collection.pk,)),
            {
                "imageData": simplejson.dumps([
                    {
                        "image_pk": image1.pk,
                        "value": "a=1\nb=9"
                    },
                    {
                        "image_pk": image2.pk,
                        "value": "a=2\nb=10"
                    }
                ])
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        image1 = Image.objects.get(pk=image1.pk)
        image2 = Image.objects.get(pk=image2.pk)

        self.assertEqual(2, image1.keyvaluetags.count())
        self.assertEqual("9", image1.keyvaluetags.get(key="b").value)

        self.assertEqual(2, image2.keyvaluetags.count())
        self.assertEqual("10", image2.keyvaluetags.get(key="b").value)

    def test_collection_navigation_links(self):
        self.client.login(username='test', password='password')
        self._create_collection(self.user, 'test_collection', 'test_description')

        self._do_upload('astrobin/fixtures/test.jpg')
        image1 = self._get_last_image()
        image1.moderator_decision = ModeratorDecision.APPROVED
        image1.save()
        Generators.key_value_tag(image=image1, key="a", value=2)

        self._do_upload('astrobin/fixtures/test.jpg')
        image2 = self._get_last_image()
        image2.moderator_decision = ModeratorDecision.APPROVED
        image2.save()
        Generators.key_value_tag(image=image2, key="a", value=1)

        collection = self._get_last_collection()
        collection.images.add(image1, image2)

        response = self.client.get(
            reverse('image_detail', args=(image1.get_id(),)) + "?nc=collection&nce=" + str(collection.pk))

        self.assertContains(response, "data-test=\"image-prev-none\"")
        self.assertContains(response, "data-test=\"image-next-" + image2.get_id() + "\"")

        collection.order_by_tag = "a"
        collection.save()

        response = self.client.get(
            reverse('image_detail', args=(image1.get_id(),)) + "?nc=collection&nce=" + str(collection.pk))

        self.assertContains(response, "data-test=\"image-prev-" + image2.get_id() + "\"")
        self.assertContains(response, "data-test=\"image-next-none\"")

    def test_collection_image_count(self):
        collection = Collection.objects.create(user=self.user)
        image = Generators.image(user=self.user)

        collection.images.add(image)
        collection.update_counts()  # Need to manually update counts since we removed the signal
        collection.refresh_from_db()

        self.assertEqual(collection.image_count, 1)
        self.assertEqual(collection.image_count_including_wip, 1)

        collection.images.clear()
        collection.update_counts()
        collection.refresh_from_db()

        self.assertEqual(collection.image_count, 0)
        self.assertEqual(collection.image_count_including_wip, 0)
        self.assertEqual(collection.image_count_including_wip, 0)

    def test_collection_image_count_reverse(self):
        collection = Collection.objects.create(user=self.user)
        image = Generators.image(user=self.user)

        image.collections.add(collection)
        collection.update_counts()  # Need to manually update counts since we removed the signal
        collection.refresh_from_db()
        image.refresh_from_db()

        self.assertEqual(collection.image_count, 1)
        self.assertEqual(collection.image_count_including_wip, 1)

        image.collections.clear()
        collection.update_counts()
        collection.refresh_from_db()

        self.assertEqual(collection.image_count, 0)
        self.assertEqual(collection.image_count_including_wip, 0)

    def test_collection_nested_collection_count(self):
        collection = Collection.objects.create(user=self.user, name="collection")
        nested_collection = Collection.objects.create(user=self.user, parent=collection, name="nested")

        collection.refresh_from_db()

        self.assertEqual(collection.nested_collection_count, 1)
        self.assertEqual(nested_collection.nested_collection_count, 0)

        nested_collection.delete()
        collection.refresh_from_db()

        self.assertEqual(collection.nested_collection_count, 0)

    def test_deleting_image_updates_collection_counts(self):
        collection = Collection.objects.create(user=self.user)
        image = Generators.image(user=self.user)

        collection.images.add(image)
        collection.update_counts()
        image.refresh_from_db()
        collection.refresh_from_db()

        self.assertEqual(collection.image_count, 1)
        self.assertEqual(collection.image_count_including_wip, 1)

        image.delete()
        collection.update_counts()
        collection.refresh_from_db()

        self.assertEqual(collection.images.count(), 0)
        self.assertEqual(Image.all_objects.filter(collections=collection).count(), 0)
        self.assertEqual(collection.image_count, 0)
        self.assertEqual(collection.image_count_including_wip, 0)

    def test_set_cover_image_anon(self):
        collection = Collection.objects.create(user=Generators.user())
        image = Generators.image(user=collection.user)

        collection.images.add(image)
        collection.refresh_from_db()

        self.assertIsNone(collection.cover)

        response = self.client.post(
            f'/api/v2/astrobin/collection/{collection.pk}/set-cover-image/',
            data=json.dumps(
                {
                    'image': image.pk,
                }
            ),
            content_type='application/json',
            follow=True,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 401)

    def test_set_cover_image_not_collection_owner(self):
        collection = Collection.objects.create(user=Generators.user())
        image = Generators.image(user=collection.user)
        other_user = Generators.user()

        collection.images.add(image)
        collection.refresh_from_db()

        self.assertIsNone(collection.cover)

        self.client.force_login(other_user)
        response = self.client.post(
            f'/api/v2/astrobin/collection/{collection.pk}/set-cover-image/',
            data=json.dumps(
                {
                    'image': image.pk,
                }
            ),
            content_type='application/json',
            follow=True,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 403)

    def test_set_cover_image_not_image_owner(self):
        collection = Collection.objects.create(user=Generators.user())
        image = Generators.image(user=Generators.user())

        collection.images.add(image)
        collection.refresh_from_db()

        self.assertIsNone(collection.cover)

        self.client.force_login(collection.user)
        response = self.client.post(
            f'/api/v2/astrobin/collection/{collection.pk}/set-cover-image/',
            data=json.dumps(
                {
                    'image': image.pk,
                }
            ),
            content_type='application/json',
            follow=True,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 400)

    def test_set_cover_image_when_image_does_not_exist(self):
        collection = Collection.objects.create(user=Generators.user())

        self.assertIsNone(collection.cover)

        self.client.force_login(collection.user)
        response = self.client.post(
            f'/api/v2/astrobin/collection/{collection.pk}/set-cover-image/',
            data=json.dumps(
                {
                    'image': 999,
                }
            ),
            content_type='application/json',
            follow=True,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 400)

    def test_set_cover_image_when_image_is_not_in_collection(self):
        collection = Collection.objects.create(user=Generators.user())
        image = Generators.image(user=collection.user)
        self.assertIsNone(collection.cover)

        self.client.force_login(collection.user)
        response = self.client.post(
            f'/api/v2/astrobin/collection/{collection.pk}/set-cover-image/',
            data=json.dumps(
                {
                    'image': image.pk,
                }
            ),
            content_type='application/json',
            follow=True,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 400)

    def test_set_cover_image(self):
        collection = Collection.objects.create(user=Generators.user())
        image = Generators.image(user=collection.user)

        collection.images.add(image)
        collection.refresh_from_db()

        self.assertIsNone(collection.cover)

        self.client.force_login(collection.user)
        response = self.client.post(
            f'/api/v2/astrobin/collection/{collection.pk}/set-cover-image/',
            data=json.dumps(
                {
                    'image': image.pk,
                }
            ),
            content_type='application/json',
            follow=True,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        collection.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(collection.cover, image)
