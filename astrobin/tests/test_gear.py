# Django
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
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
        self.assertEqual(g.__unicode__(), "Test make Test name")
        g.delete()

        g, created = Gear.objects.get_or_create(
            make = "Test",
            name = "Test name")
        self.assertEqual(g.__unicode__(), "Test name")
        g.delete()

        g, created = Gear.objects.get_or_create(
            make = "",
            name = "Test name")
        self.assertEqual(g.__unicode__(), "Test name")
        g.delete()

    def test_attributes(self):
        g, created = Gear.objects.get_or_create(
            name = "Test name")
        self.assertEqual(g.attributes(), [])
        g.delete()

    def test_slug(self):
        g, created = Gear.objects.get_or_create(
            make = "Test make",
            name = "Test name")
        self.assertEqual(g.slug(), "test-make-test-name")
        g.delete()

    def test_get_absolute_url(self):
         g, created = Gear.objects.get_or_create(
            make = "Test make",
            name = "Test name")
         self.assertEqual(
            g.get_absolute_url(),
            '/gear/%i/test-make-test-name/' % g.id)
         g.delete()

    def test_hard_merge(self):
        # Check with diffrent gear types
        g1, created = Telescope.objects.get_or_create(name = "1")
        g2, created = Camera.objects.get_or_create(name = "2")
        g1.hard_merge(g2)
        self.assertEqual(Gear.objects.filter(name = "2").count(), 1)
        g1.delete()
        g2.delete()

        # Check successful merge
        g1, created = Filter.objects.get_or_create(name = "1")
        g2, created = Filter.objects.get_or_create(name = "2")

        # Assign slave to profile
        u = User.objects.create_user('test', 'test@test.com', 'password')
        u.userprofile.filters.add(g2)
        u.userprofile.save(keep_deleted=True)

        # Assign slave to image
        i, created  = Image.objects.get_or_create(user = u)
        i.filters.add(g2)
        i.save(keep_deleted=True)

        # Check DSA too
        dsa, created = DeepSky_Acquisition.objects.get_or_create(
            image = i, filter = g2)

        g1.hard_merge(g2)

        self.assertEqual(Gear.objects.filter(name = "2").count(), 0)
        self.assertEqual(u.userprofile.filters.all()[0], g1)
        self.assertEqual(i.filters.all()[0], g1)

        dsa = DeepSky_Acquisition.objects.get(pk = dsa.pk)
        self.assertEqual(dsa.filter, g1)

        g1.delete()
        i.delete()
        u.delete()


    ###########################################################################
    # VIEW TESTS                                                              #
    ###########################################################################

    def test_gear_page_view(self):
        g, created = Telescope.objects.get_or_create(name = "Test telescope")
        response = self.client.get(reverse('gear_page', kwargs = {'id': g.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h1>Test telescope</h1>", html = True)

