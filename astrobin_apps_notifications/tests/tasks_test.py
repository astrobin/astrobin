import mock
from django.test import TestCase, override_settings

from astrobin.tests.generators import Generators
from astrobin_apps_images.services import ImageService
from toggleproperties.models import ToggleProperty


class TasksTest(TestCase):
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @mock.patch('astrobin_apps_notifications.tasks.push_notification')
    def test_new_image_notification(self, push_notification):
        user = Generators.user()
        follower = Generators.user()

        ToggleProperty.objects.create(
            property_type='follow',
            user=follower,
            content_object=user
        )

        Generators.image(user=user)

        push_notification.assert_called_with([follower], user, 'new_image', mock.ANY)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @mock.patch('astrobin_apps_notifications.tasks.push_notification')
    def test_new_image_notification_collaborators(self, push_notification):
        user = Generators.user()
        collaborator = Generators.user()

        user_follower = Generators.user()
        collaborator_follower = Generators.user()

        ToggleProperty.objects.create(
            property_type='follow',
            user=user_follower,
            content_object=user
        )
        ToggleProperty.objects.create(
            property_type='follow',
            user=collaborator_follower,
            content_object=collaborator
        )

        image = Generators.image(user=user, is_wip=True)
        image.collaborators.add(collaborator)
        ImageService(image).promote_to_public_area(skip_notifications=False)

        push_notification.assert_called_with([user_follower, collaborator_follower], user, 'new_image', mock.ANY)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @mock.patch('astrobin_apps_notifications.tasks.push_notification')
    def test_new_image_notification_collaborators_no_duplicates(self, push_notification):
        user = Generators.user()
        collaborator1 = Generators.user()
        collaborator2 = Generators.user()

        follower = Generators.user()

        ToggleProperty.objects.create(
            property_type='follow',
            user=follower,
            content_object=user
        )
        ToggleProperty.objects.create(
            property_type='follow',
            user=follower,
            content_object=collaborator1
        )
        ToggleProperty.objects.create(
            property_type='follow',
            user=follower,
            content_object=collaborator2
        )

        image = Generators.image(user=user, is_wip=True)
        image.collaborators.add(collaborator1)
        ImageService(image).promote_to_public_area(skip_notifications=False)

        push_notification.assert_called_with([follower], user, 'new_image', mock.ANY)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @mock.patch('astrobin_apps_notifications.tasks.push_notification')
    def test_new_image_revision_notification(self, push_notification):
        user = Generators.user()
        follower = Generators.user()

        ToggleProperty.objects.create(
            property_type='follow',
            user=follower,
            content_object=user
        )

        image = Generators.image(user=user)
        Generators.imageRevision(image=image)

        push_notification.assert_called_with([follower], user, 'new_image_revision', mock.ANY)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @mock.patch('astrobin_apps_notifications.tasks.push_notification')
    def test_new_image_revision_notification_collaborators(self, push_notification):
        user = Generators.user()
        collaborator = Generators.user()

        user_follower = Generators.user()
        collaborator_follower = Generators.user()

        ToggleProperty.objects.create(
            property_type='follow',
            user=user_follower,
            content_object=user
        )
        ToggleProperty.objects.create(
            property_type='follow',
            user=collaborator_follower,
            content_object=collaborator
        )

        image = Generators.image(user=user)
        image.collaborators.add(collaborator)
        Generators.imageRevision(image=image)

        push_notification.assert_called_with([user_follower, collaborator_follower], user, 'new_image_revision', mock.ANY)
