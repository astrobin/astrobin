from django.test import TestCase

from astrobin_apps_equipment.tests.equipment_generators import EquipmentGenerators


class TestEquipmentItem(TestCase):
    def test_str_when_diy(self):
        camera = EquipmentGenerators.camera(brand=None, name="Test")
        self.assertEquals("DIY Test", str(camera))

    def test_str_when_unspecified_company(self):
        telescope = EquipmentGenerators.telescope(
            brand=EquipmentGenerators.brand(name="Unspecified/unknown company"),
            name="Test"
        )
        self.assertEquals("Test", str(telescope))

    def test_str_when_brand_name_equals_name(self):
        telescope = EquipmentGenerators.telescope(
            brand=EquipmentGenerators.brand(name="Test"),
            name="Test"
        )
        self.assertEquals("Test", str(telescope))

    def test_str(self):
        mount = EquipmentGenerators.mount(
            brand=EquipmentGenerators.brand(name="Brand"),
            name="Test"
        )
        self.assertEquals("Brand Test", str(mount))
