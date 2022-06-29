from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from astrobin.tests.generators import Generators
from astrobin_apps_equipment.models import Camera
from astrobin_apps_equipment.models.camera_base_model import CameraType
from astrobin_apps_equipment.models.equipment_item_group import EquipmentItemKlass, EquipmentItemUsageType
from astrobin_apps_equipment.tests.equipment_generators import EquipmentGenerators


class TestApiCameraViewSet(TestCase):
    def test_list_with_no_items(self):
        client = APIClient()

        response = client.get(reverse('astrobin_apps_equipment:camera-list'), format='json')
        self.assertEquals(0, response.data['count'])

    def test_list_with_items(self):
        client = APIClient()

        camera = EquipmentGenerators.camera()

        response = client.get(reverse('astrobin_apps_equipment:camera-list'), format='json')
        self.assertEquals(1, response.data['count'])
        self.assertEquals(camera.name, response.data['results'][0]['name'])

    def test_deleting_not_allowed(self):
        client = APIClient()

        camera = EquipmentGenerators.camera()

        response = client.delete(reverse('astrobin_apps_equipment:camera-detail', args=(camera.pk,)), format='json')
        self.assertEquals(405, response.status_code)

        user = Generators.user(groups=['equipment_moderators'])
        client.login(username=user.username, password=user.password)
        client.force_authenticate(user=user)

        response = client.delete(reverse('astrobin_apps_equipment:camera-detail', args=(camera.pk,)), format='json')
        self.assertEquals(405, response.status_code)

    def test_post_not_allowed(self):
        client = APIClient()

        response = client.post(reverse('astrobin_apps_equipment:camera-list'), {
            'brand': EquipmentGenerators.brand().pk,
            'sensor': EquipmentGenerators.sensor().pk,
            'name': 'Camera Foo',
            'type': CameraType.DEDICATED_DEEP_SKY,
        }, format='json')
        self.assertEquals(403, response.status_code)

        user = Generators.user()
        client.login(username=user.username, password=user.password)
        client.force_authenticate(user=user)

        response = client.post(reverse('astrobin_apps_equipment:camera-list'), {
            'brand': EquipmentGenerators.brand().pk,
            'sensor': EquipmentGenerators.sensor().pk,
            'name': 'Camera Foo',
            'type': CameraType.DEDICATED_DEEP_SKY,
        }, format='json')
        self.assertEquals(403, response.status_code)

    def test_created_by(self):
        client = APIClient()

        user = Generators.user(groups=['equipment_moderators'])
        client.login(username=user.username, password=user.password)
        client.force_authenticate(user=user)

        response = client.post(reverse('astrobin_apps_equipment:camera-list'), {
            'brand': EquipmentGenerators.brand().pk,
            'sensor': EquipmentGenerators.sensor().pk,
            'name': 'Camera Foo',
            'type': CameraType.DEDICATED_DEEP_SKY,
        }, format='json')
        self.assertEquals(201, response.status_code)
        self.assertEquals(user.pk, response.data['created_by'])

    def test_list_returns_only_own_DIYs(self):
        user = Generators.user()
        first = EquipmentGenerators.camera(created_by=user)
        first.brand = None
        first.save()

        second = EquipmentGenerators.camera()
        second.brand = None
        second.save()

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get(reverse('astrobin_apps_equipment:camera-list'), format='json')
        self.assertEquals(1, response.data['count'])
        self.assertEquals(first.name, response.data['results'][0]['name'])

    def test_find_recently_used_no_usages(self):
        user = Generators.user()

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get(
            reverse('astrobin_apps_equipment:camera-list') + 'recently-used/?usage-type=imaging', format='json'
        )

        self.assertEquals(0, len(response.data))

    def test_find_recently_used_one_usage(self):
        user = Generators.user()
        camera = EquipmentGenerators.camera(created_by=user)
        image = Generators.image(user=user)
        image.imaging_cameras_2.add(camera)

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get(
            reverse('astrobin_apps_equipment:camera-list') + 'recently-used/?usage-type=imaging', format='json'
        )

        self.assertEquals(1, len(response.data))

    def test_find_recently_used_wrong_usage_type(self):
        user = Generators.user()
        camera = EquipmentGenerators.camera(created_by=user)
        image = Generators.image(user=user)
        image.imaging_cameras_2.add(camera)

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get(
            reverse('astrobin_apps_equipment:camera-list') + 'recently-used/?usage-type=guiding', format='json'
        )

        self.assertEquals(0, len(response.data))

    def test_modified_camera_cannot_be_approved(self):
        camera = EquipmentGenerators.camera(type=CameraType.DSLR_MIRRORLESS)
        modified = Camera.objects.get(brand=camera.brand, name=camera.name, modified=True, cooled=False)

        client = APIClient()
        client.force_authenticate(user=Generators.user(groups=['equipment_moderators']))

        response = client.post(
            reverse('astrobin_apps_equipment:camera-detail', args=(modified.pk,)) + 'approve/', format='json'
        )

        self.assertEquals(400, response.status_code)

    def test_modified_camera_cannot_be_rejected(self):
        camera = EquipmentGenerators.camera(type=CameraType.DSLR_MIRRORLESS)
        modified = Camera.objects.get(brand=camera.brand, name=camera.name, modified=True, cooled=False)

        client = APIClient()
        client.force_authenticate(user=Generators.user(groups=['equipment_moderators']))

        response = client.post(
            reverse('astrobin_apps_equipment:camera-detail', args=(modified.pk,)) + 'reject/', format='json'
        )

        self.assertEquals(400, response.status_code)

    def test_brand_and_variant_of_brand_mismatch(self):
        client = APIClient()
        client.force_authenticate(user=Generators.user(groups=['equipment_moderators']))

        brand1 = EquipmentGenerators.brand()
        brand2 = EquipmentGenerators.brand()
        camera = EquipmentGenerators.camera(brand=brand1)

        response = client.post(
            reverse('astrobin_apps_equipment:camera-list'), {
                'brand': brand2.pk,
                'type': CameraType.DEDICATED_DEEP_SKY,
                'name': 'Test',
                'variant_of': camera.brand.pk
            },
            format='json'
        )

        self.assertContains(response, "The variant needs to be in the same brand as the item", status_code=400)

    def test_diy_does_not_allow_variants(self):
        client = APIClient()
        client.force_authenticate(user=Generators.user(groups=['equipment_moderators']))

        camera = EquipmentGenerators.camera()

        response = client.post(
            reverse('astrobin_apps_equipment:camera-list'), {
                'brand': None,
                'type': CameraType.DEDICATED_DEEP_SKY,
                'name': 'Test',
                'variant_of': camera.brand.pk
            },
            format='json'
        )

        self.assertContains(response, "DIY items do not support variants", status_code=400)

    def test_circular_variants(self):
        client = APIClient()
        client.force_authenticate(user=Generators.user(groups=['equipment_moderators']))

        brand = EquipmentGenerators.brand()
        camera = EquipmentGenerators.camera(brand=brand)
        variant = EquipmentGenerators.camera(brand=brand, variant_of=camera)

        response = client.post(
            reverse('astrobin_apps_equipment:camera-list'), {
                'brand': brand.pk,
                'type': CameraType.DEDICATED_DEEP_SKY,
                'name': 'Test',
                'variant_of': variant.pk
            },
            format='json'
        )

        self.assertContains(response, "Variants do not support variants", status_code=400)

    def test_dslr_mirrorless_does_not_allow_variants(self):
        client = APIClient()
        client.force_authenticate(user=Generators.user(groups=['equipment_moderators']))

        camera = EquipmentGenerators.camera()

        response = client.post(
            reverse('astrobin_apps_equipment:camera-list'), {
                'brand': EquipmentGenerators.brand().id,
                'type': CameraType.DSLR_MIRRORLESS,
                'name': 'Test',
                'variant_of': camera.pk
            },
            format='json'
        )

        self.assertContains(response, "DSLR/Mirrorless cameras do not support variants", status_code=400)

    def test_reject_as_duplicate(self):
        client = APIClient()

        user = Generators.user(groups=['own_equipment_migrators'])
        camera = EquipmentGenerators.camera(type=CameraType.DEDICATED_DEEP_SKY)
        duplicate = EquipmentGenerators.camera(type=CameraType.DEDICATED_DEEP_SKY)
        image = Generators.image(user=user)
        image.imaging_cameras_2.add(duplicate)

        client.force_authenticate(user=Generators.user(groups=['equipment_moderators']))

        response = client.post(
            reverse('astrobin_apps_equipment:camera-detail', args=(duplicate.id,)) + 'reject/', {
                'reason': 'DUPLICATE',
                'duplicate_of_klass': EquipmentItemKlass.CAMERA,
                'duplicate_of_usage_type': EquipmentItemUsageType.IMAGING,
                'duplicate_of': camera.id,
            }, format='json'
        )

        self.assertEquals(200, response.status_code)
        self.assertFalse(Camera.objects.filter(id=duplicate.id).exists())
        self.assertTrue(camera in image.imaging_cameras_2.all())

    def test_reject_as_duplicate_dslr(self):
        client = APIClient()

        user = Generators.user(groups=['own_equipment_migrators'])
        camera = EquipmentGenerators.camera(type=CameraType.DSLR_MIRRORLESS, modified=False, cooled=False)
        duplicate = EquipmentGenerators.camera(type=CameraType.DSLR_MIRRORLESS, modified=False, cooled=False)
        image = Generators.image(user=user)
        image.imaging_cameras_2.add(duplicate)

        client.force_authenticate(user=Generators.user(groups=['equipment_moderators']))

        response = client.post(
            reverse('astrobin_apps_equipment:camera-detail', args=(duplicate.id,)) + 'reject/', {
                'reason': 'DUPLICATE',
                'duplicate_of_klass': EquipmentItemKlass.CAMERA,
                'duplicate_of_usage_type': EquipmentItemUsageType.IMAGING,
                'duplicate_of': camera.id,
            }, format='json'
        )

        self.assertEquals(200, response.status_code)
        self.assertFalse(Camera.objects.filter(brand=duplicate.brand, name=duplicate.name))
        self.assertTrue(camera in image.imaging_cameras_2.all())

    def test_reject_as_duplicate_modified_dslr(self):
        client = APIClient()

        user = Generators.user(groups=['own_equipment_migrators'])
        camera = EquipmentGenerators.camera(type=CameraType.DSLR_MIRRORLESS, modified=False, cooled=False)
        modified = Camera.objects.get(brand=camera.brand, name=camera.name, modified=True, cooled=False)
        duplicate = EquipmentGenerators.camera(type=CameraType.DSLR_MIRRORLESS, cooled=False)
        modified_duplicate = Camera.objects.get(brand=duplicate.brand, name=duplicate.name, modified=True, cooled=False)
        image = Generators.image(user=user)
        image.imaging_cameras_2.add(modified_duplicate)

        client.force_authenticate(user=Generators.user(groups=['equipment_moderators']))

        response = client.post(
            reverse('astrobin_apps_equipment:camera-detail', args=(duplicate.id,)) + 'reject/', {
                'reason': 'DUPLICATE',
                'duplicate_of_klass': EquipmentItemKlass.CAMERA,
                'duplicate_of_usage_type': EquipmentItemUsageType.IMAGING,
                'duplicate_of': modified.id,
            }, format='json'
        )

        self.assertEquals(200, response.status_code)
        self.assertFalse(Camera.objects.filter(brand=duplicate.brand, name=duplicate.name))
        self.assertTrue(modified in image.imaging_cameras_2.all())

    def test_reject_as_duplicate_modified_dslr_matches_attributes(self):
        client = APIClient()

        user = Generators.user(groups=['own_equipment_migrators'])
        camera = EquipmentGenerators.camera(type=CameraType.DSLR_MIRRORLESS, modified=False, cooled=False)
        modified = Camera.objects.get(brand=camera.brand, name=camera.name, modified=True, cooled=False)
        duplicate = EquipmentGenerators.camera(type=CameraType.DSLR_MIRRORLESS, cooled=False)
        modified_duplicate = Camera.objects.get(brand=duplicate.brand, name=duplicate.name, modified=True, cooled=False)
        image = Generators.image(user=user)
        image.imaging_cameras_2.add(modified_duplicate)

        client.force_authenticate(user=Generators.user(groups=['equipment_moderators']))

        response = client.post(
            reverse('astrobin_apps_equipment:camera-detail', args=(duplicate.id,)) + 'reject/', {
                'reason': 'DUPLICATE',
                'duplicate_of_klass': EquipmentItemKlass.CAMERA,
                'duplicate_of_usage_type': EquipmentItemUsageType.IMAGING,
                'duplicate_of': camera.id,
            }, format='json'
        )

        self.assertEquals(200, response.status_code)
        self.assertFalse(Camera.objects.filter(brand=duplicate.brand, name=duplicate.name))
        self.assertTrue(modified in image.imaging_cameras_2.all())

    def test_reject_as_duplicate_of_modified_dslr(self):
        client = APIClient()

        user = Generators.user(groups=['own_equipment_migrators'])
        camera = EquipmentGenerators.camera(type=CameraType.DSLR_MIRRORLESS, modified=False, cooled=False)
        modified = Camera.objects.get(brand=camera.brand, name=camera.name, modified=True, cooled=False)
        duplicate = EquipmentGenerators.camera(type=CameraType.DEDICATED_DEEP_SKY)
        image = Generators.image(user=user)
        image.imaging_cameras_2.add(duplicate)

        client.force_authenticate(user=Generators.user(groups=['equipment_moderators']))

        response = client.post(
            reverse('astrobin_apps_equipment:camera-detail', args=(duplicate.id,)) + 'reject/', {
                'reason': 'DUPLICATE',
                'duplicate_of_klass': EquipmentItemKlass.CAMERA,
                'duplicate_of_usage_type': EquipmentItemUsageType.IMAGING,
                'duplicate_of': modified.id,
            }, format='json'
        )

        self.assertEquals(200, response.status_code)
        self.assertFalse(Camera.objects.filter(brand=duplicate.brand, name=duplicate.name))
        self.assertTrue(modified in image.imaging_cameras_2.all())
