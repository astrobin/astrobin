# Django
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase

# AstroBin
from astrobin.models import (
    Image,
    DeepSky_Acquisition,
    Gear,
    Telescope,
    Camera,
    Filter)


class GearTest(TestCase):
    ###########################################################################
    # MODEL TESTS                                                             #
    ###########################################################################

    def test_get_make(self):
        g = Gear.objects.create(
            make = "Test make",
            name = "Test name")
        self.assertEqual(g.get_make(), "Test make")

    def test_get_name(self):
        g = Gear.objects.create(
            name = "Test name")
        self.assertEqual(g.get_name(), "Test name")

    def test_unicode(self):
        g, created = Gear.objects.get_or_create(
            make = "Test make",
            name = "Test name")
        self.assertEqual(str(g), "Test make Test name")
        g.delete()

        g, created = Gear.objects.get_or_create(
            make = "Test",
            name = "Test name")
        self.assertEqual(str(g), "Test name")
        g.delete()

        g, created = Gear.objects.get_or_create(
            make = "",
            name = "Test name")
        self.assertEqual(str(g), "Test name")

    def test_attributes(self):
        g, created = Gear.objects.get_or_create(
            name = "Test name")
        self.assertEqual(g.attributes(), [])

    def test_slug(self):
        g, created = Gear.objects.get_or_create(
            make = "Test make",
            name = "Test name")
        self.assertEqual(g.slug(), "test-make-test-name")

    def test_get_absolute_url(self):
         g, created = Gear.objects.get_or_create(make = "Test make", name = "Test name")
         self.assertEqual('/search/?q=Test make Test name', g.get_absolute_url())
