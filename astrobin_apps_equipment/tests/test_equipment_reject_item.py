from django.test import TestCase

from astrobin.models import DeepSky_Acquisition
from astrobin.tests.generators import Generators
from astrobin_apps_equipment.models.equipment_item import EquipmentItemRejectionReason, EquipmentItemReviewerDecision
from astrobin_apps_equipment.models.equipment_item_group import EquipmentItemKlass
from astrobin_apps_equipment.services import EquipmentService
from astrobin_apps_equipment.tests.equipment_generators import EquipmentGenerators


class EquipmentServiceRejectItemTest(TestCase):
    def test_reject_filter_as_duplicate(self):
        user = Generators.user()
        image = Generators.image(user=user)
        filter_ = EquipmentGenerators.filter()
        duplicate = EquipmentGenerators.filter()

        image.filters_2.add(duplicate)
        DeepSky_Acquisition.objects.create(image=image, filter_2=duplicate, number=10, duration=300)

        duplicate.reviewer_decision = EquipmentItemReviewerDecision.REJECTED
        duplicate.reviewer_rejection_reason = EquipmentItemRejectionReason.DUPLICATE
        duplicate.reviewer_rejection_duplicate_of_klass = EquipmentItemKlass.FILTER
        duplicate.reviewer_rejection_duplicate_of = filter_.id
        duplicate.save()

        EquipmentService.reject_item(duplicate)

        self.assertFalse(image.filters_2.filter(pk=duplicate.pk).exists())
        self.assertTrue(image.filters_2.filter(pk=filter_.pk).exists())
        self.assertFalse(DeepSky_Acquisition.objects.filter(image=image, filter_2=duplicate).exists())
        self.assertTrue(DeepSky_Acquisition.objects.filter(image=image, filter_2=filter_).exists())
