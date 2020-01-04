import re

import simplejson
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from mock import patch

from astrobin.models import Collection
from astrobin.models import Image
from astrobin_apps_images.models import KeyValueTag


class CollectionTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test', 'test@test.com', 'password')
        self.user2 = User.objects.create_user('test2', 'test@test.com', 'password')

        self.user.default_gallery_section = 5
        self.user.save()

    def tearDown(self):
        self.user.delete()
        self.user2.delete()

    ###########################################################################
    # HELPERS                                                                 #
    ###########################################################################

    def _do_upload(self, filename, wip=False):
        data = {'image_file': open(filename, 'rb')}
        if wip:
            data['wip'] = True

        patch('astrobin.tasks.retrieve_primary_thumbnails.delay')
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

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_collections_list_view(self, retrieve_primary_thumbnails):
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
        self.assertEquals(collection.name, 'test_collection')
        self.assertEquals(collection.description, 'test_description')
        response = self.client.get(reverse('user_collections_list', args=(self.user.username,)))
        self.assertContains(response, "test_collection")

        # Collection has no images
        self.assertContains(response, "collection-image empty")

        image.delete()
        collection.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_collection_update_view(self, retrieve_primary_thumbnails):
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
        self.assertIsNotNone(re.search(r'data-id="%d"\s+data-alias="%s"' % (image2.pk, "collection"), response.content))

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
        self.assertIsNotNone(re.search(r'data-id="%d"\s+data-alias="%s"' % (image1.pk, "collection"), response.content))

        image1.delete()
        image2.delete()
        collection.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_collection_delete_view(self, retrieve_primary_thumbnails):
        # Create a collection
        self.client.login(username='test', password='password')
        self._do_upload('astrobin/fixtures/test.jpg')
        self._create_collection(self.user, 'test_collection', 'test_description')
        image = self._get_last_image()
        collection = self._get_last_collection()
        response = self.client.post(
            reverse('user_collections_delete', args=(self.user.username, collection.pk)),
            follow=True)
        self.assertNotContains(response, "test_collection")

        image.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_collection_add_remove_images_view(self, retrieve_primary_thumbnails):
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

        image.delete()
        image2.delete()
        collection.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_collection_order_by_tag(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._create_collection(self.user, 'test_collection', 'test_description')

        self._do_upload('astrobin/fixtures/test.jpg')
        image1 = self._get_last_image()
        KeyValueTag.objects.create(image=image1, key="a", value=1)
        KeyValueTag.objects.create(image=image1, key="b", value=2)

        self._do_upload('astrobin/fixtures/test.jpg')
        image2 = self._get_last_image()
        KeyValueTag.objects.create(image=image2, key="a", value=2)
        KeyValueTag.objects.create(image=image2, key="b", value=1)

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

        image1.delete()
        image2.delete()
        collection.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_collection_quick_edit_key_value_tags(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._create_collection(self.user, 'test_collection', 'test_description')

        self._do_upload('astrobin/fixtures/test.jpg')
        image1 = self._get_last_image()
        KeyValueTag.objects.create(image=image1, key="a", value=1)

        self._do_upload('astrobin/fixtures/test.jpg')
        image2 = self._get_last_image()
        KeyValueTag.objects.create(image=image2, key="a", value=2)

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
        self.assertEqual("10", image2   .keyvaluetags.get(key="b").value)

        image1.delete()
        image2.delete()
        collection.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_collection_navigation_links(self, retrieve_primary_thumbnails):
        self.client.login(username='test', password='password')
        self._create_collection(self.user, 'test_collection', 'test_description')

        self._do_upload('astrobin/fixtures/test.jpg')
        image1 = self._get_last_image()
        KeyValueTag.objects.create(image=image1, key="a", value=2)

        self._do_upload('astrobin/fixtures/test.jpg')
        image2 = self._get_last_image()
        KeyValueTag.objects.create(image=image2, key="a", value=1)

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

        image1.delete()
        image2.delete()
        collection.delete()
