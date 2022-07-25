
from django.test import TestCase
import mock

from astrobin.tests.generators import Generators
from astrobin_apps_equipment.models.equipment_item import EquipmentItemReviewerDecision
from astrobin_apps_equipment.tests.equipment_generators import EquipmentGenerators


class TestTopicSaveSignals(TestCase):
    @mock.patch('astrobin_apps_forum.services.forum_service.push_notification')
    def test_notification_for_equipment_item_topics(self, push_notification):
        user1 = Generators.user()
        user2 = Generators.user()

        image1 = Generators.image(user=user1)
        Generators.image(user=user2)

        telescope = EquipmentGenerators.telescope(reviewer_decision=EquipmentItemReviewerDecision.APPROVED)
        image1.imaging_telescopes_2.add(telescope)

        forum = telescope.forum

        self.assertIsNotNone(forum)

        topic = Generators.forum_topic(forum=forum)

        push_notification.assert_has_calls(
            [
                mock.call([user1], topic.user, 'new_topic_for_equipment_you_use', mock.ANY),
            ], any_order=True
        )
