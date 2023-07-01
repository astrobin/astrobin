import mock
from django.test import TestCase, override_settings

from astrobin.tests.generators import Generators
from astrobin_apps_equipment.tests.equipment_generators import EquipmentGenerators
from astrobin_apps_images.services import ImageService


class TasksTest(TestCase):
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @mock.patch('astrobin_apps_notifications.tasks.push_notification')
    def test_new_image_notification(self, push_notification):
        user = Generators.user()
        follower = Generators.user()

        Generators.follow(user, user=follower)

        image = Generators.image(user=user)

        push_notification.assert_called_with([follower], user, 'new_image', {
            'image': image,
            'image_thumbnail': mock.ANY,
            'followed_equipment_items': [],
        })

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @mock.patch('astrobin_apps_notifications.tasks.push_notification')
    def test_new_image_from_equipment_item_notification(self, push_notification):
        user = Generators.user()
        user_follower = Generators.user()
        telescope_follower = Generators.user()
        telescope = EquipmentGenerators.telescope()

        Generators.follow(user, user=user_follower)
        Generators.follow(telescope, user=telescope_follower)

        image = Generators.image(user=user, is_wip=True)
        image.imaging_telescopes_2.add(telescope)

        ImageService(image).promote_to_public_area(skip_notifications=False)
        image.save()

        push_notification.assert_has_calls([
            mock.call([user_follower], user, 'new_image', {
                'image': image,
                'image_thumbnail': mock.ANY,
                'followed_equipment_items': [],
            }),
            mock.call([telescope_follower], user, 'new-image-from-followed-equipment', {
                'image': image,
                'image_thumbnail': mock.ANY,
                'items': [telescope],
            })
        ], any_order=True)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @mock.patch('astrobin_apps_notifications.tasks.push_notification')
    def test_new_image_from_equipment_item_notification_avoids_duplicate_if_new_image_is_sent(self, push_notification):
        user = Generators.user()
        follower = Generators.user()
        telescope = EquipmentGenerators.telescope()

        Generators.follow(user, user=follower)
        Generators.follow(telescope, user=follower)

        image = Generators.image(user=user, is_wip=True)
        image.imaging_telescopes_2.add(telescope)

        ImageService(image).promote_to_public_area(skip_notifications=False)
        image.save()

        self.assertEquals(push_notification.call_count, 1)
        push_notification.assert_has_calls(
            [
                mock.call([follower], user, 'new_image', {
                    'image': image,
                    'image_thumbnail': mock.ANY,
                    'followed_equipment_items': [telescope],
                }),
            ]
        )

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @mock.patch('astrobin_apps_notifications.tasks.push_notification')
    def test_new_image_from_equipment_item_notification_avoids_duplicate_if_new_image_is_sent_for_collaborator(self, push_notification):
        user = Generators.user()
        collaborator = Generators.user()
        follower = Generators.user()
        telescope = EquipmentGenerators.telescope()

        Generators.follow(collaborator, user=follower)
        Generators.follow(telescope, user=follower)

        image = Generators.image(user=user, is_wip=True)
        image.imaging_telescopes_2.add(telescope)
        image.collaborators.add(collaborator)

        ImageService(image).promote_to_public_area(skip_notifications=False)
        image.save()

        self.assertEquals(push_notification.call_count, 1)
        push_notification.assert_has_calls(
            [
                mock.call([follower], user, 'new_image', {
                    'image': image,
                    'image_thumbnail': mock.ANY,
                    'followed_equipment_items': [telescope],
                }),
            ]
        )

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @mock.patch('astrobin_apps_notifications.tasks.push_notification')
    def test_new_image_from_equipment_item_notification_avoid_duplicate_for_different_usage_types(self, push_notification):
        user = Generators.user()
        user_follower = Generators.user()
        telescope_follower = Generators.user()
        telescope = EquipmentGenerators.telescope()

        Generators.follow(user, user=user_follower)
        Generators.follow(telescope, user=telescope_follower)

        image = Generators.image(user=user, is_wip=True)
        image.imaging_telescopes_2.add(telescope)
        image.guiding_telescopes_2.add(telescope)

        ImageService(image).promote_to_public_area(skip_notifications=False)
        image.save()

        self.assertEquals(push_notification.call_count, 2)
        push_notification.assert_has_calls(
            [
                mock.call([user_follower], user, 'new_image', {
                    'image': image,
                    'image_thumbnail': mock.ANY,
                    'followed_equipment_items': [],
                }),
                mock.call([telescope_follower], user, 'new-image-from-followed-equipment', {
                    'image': image,
                    'image_thumbnail': mock.ANY,
                    'items': [telescope],
                })
            ], any_order=True
        )

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @mock.patch('astrobin_apps_notifications.tasks.push_notification')
    def test_new_image_from_equipment_item_notification_avoid_duplicate_for_different_classes(
            self, push_notification
    ):
        user = Generators.user()
        user_follower = Generators.user()
        equipment_follower = Generators.user()
        telescope = EquipmentGenerators.telescope()
        camera = EquipmentGenerators.camera()

        Generators.follow(user, user=user_follower)
        Generators.follow(telescope, user=equipment_follower)
        Generators.follow(camera, user=equipment_follower)

        image = Generators.image(user=user, is_wip=True)
        image.imaging_telescopes_2.add(telescope)
        image.imaging_cameras_2.add(camera)

        ImageService(image).promote_to_public_area(skip_notifications=False)
        image.save()

        self.assertEquals(push_notification.call_count, 2)
        push_notification.assert_has_calls(
            [
                mock.call([user_follower], user, 'new_image', {
                    'image': image,
                    'image_thumbnail': mock.ANY,
                    'followed_equipment_items': [],
                }),
                mock.call([equipment_follower], user, 'new-image-from-followed-equipment', {
                    'image': image,
                    'image_thumbnail': mock.ANY,
                    'items': [telescope, camera],
                })
            ], any_order=True
        )


    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @mock.patch('astrobin_apps_notifications.tasks.push_notification')
    def test_new_image_notification_collaborators(self, push_notification):
        user = Generators.user()
        collaborator = Generators.user()

        user_follower = Generators.user()
        collaborator_follower = Generators.user()

        Generators.follow(user, user=user_follower)
        Generators.follow(collaborator, user=collaborator_follower)

        image = Generators.image(user=user, is_wip=True)
        image.collaborators.add(collaborator)
        ImageService(image).promote_to_public_area(skip_notifications=False)
        image.save()

        push_notification.assert_has_calls(
            [
                mock.call(
                    [user_follower], user, 'new_image', {
                        'image': image,
                        'image_thumbnail': mock.ANY,
                        'followed_equipment_items': [],
                    }
                ),
                mock.call(
                    [collaborator_follower], user, 'new_image', {
                        'image': image,
                        'image_thumbnail': mock.ANY,
                        'followed_equipment_items': [],
                    }
                )
            ]
        )

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @mock.patch('astrobin_apps_notifications.tasks.push_notification')
    def test_new_image_notification_collaborators_no_duplicates(self, push_notification):
        user = Generators.user()
        collaborator1 = Generators.user()
        collaborator2 = Generators.user()

        follower = Generators.user()

        Generators.follow(user, user=follower)
        Generators.follow(collaborator1, user=follower)
        Generators.follow(collaborator2, user=follower)

        image = Generators.image(user=user, is_wip=True)
        image.collaborators.add(collaborator1)
        ImageService(image).promote_to_public_area(skip_notifications=False)
        image.save()

        push_notification.assert_called_with([follower], user, 'new_image', mock.ANY)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @mock.patch('astrobin_apps_notifications.tasks.push_notification')
    def test_new_image_revision_notification(self, push_notification):
        user = Generators.user()
        follower = Generators.user()

        Generators.follow(user, user=follower)

        image = Generators.image(user=user)
        Generators.image_revision(image=image)

        push_notification.assert_called_with([follower], user, 'new_image_revision', mock.ANY)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @mock.patch('astrobin_apps_notifications.tasks.push_notification')
    def test_new_image_revision_notification_collaborators(self, push_notification):
        user = Generators.user()
        collaborator = Generators.user()

        user_follower = Generators.user()
        collaborator_follower = Generators.user()

        Generators.follow(user, user=user_follower)
        Generators.follow(collaborator, user=collaborator_follower)

        image = Generators.image(user=user)
        image.collaborators.add(collaborator)
        Generators.image_revision(image=image)

        push_notification.assert_called_with([user_follower, collaborator_follower], user, 'new_image_revision', mock.ANY)
