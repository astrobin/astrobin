# Python
from datetime import date, timedelta

# Django
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.test import TestCase

# AstroBin
from astrobin.models import Image, Acquisition, Telescope


class UserTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username = "user", email = "user@example.com",
            password = "password")


    def tearDown(self):
        self.user.delete()


    def test_user_page_view(self):
        today = date.today()

        # Test simple access
        image = Image.objects.create(
            user = self.user, title = "TEST BASIC IMAGE")
        response = self.client.get(reverse('user_page', args = ('user',)))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image.title in response.content, True)
        image.delete()

        # Test staging when anonymous
        response = self.client.get(
            reverse('user_page', args = ('user',)) + '?staging')
        self.assertEquals(response.status_code, 403)

        # Test staging images
        self.client.login(username = "user", password="password")

        image = Image.objects.create(
            user = self.user, title = "TEST STAGING IMAGE", is_wip = True)
        response = self.client.get(
            reverse('user_page', args = ('user',)) + '?staging')

        self.assertEquals(response.status_code, 200)
        self.assertEquals(image.title in response.content, True)

        response = self.client.get(reverse('user_page', args = ('user',)))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image.title in response.content, False)

        image.delete()
        self.client.logout()

        # Test "upload time" sorting
        image1 = Image.objects.create(
            user = self.user, title = "IMAGE1", uploaded = today)
        image2 = Image.objects.create(
            user = self.user, title = "IMAGE2", uploaded = today + timedelta(1))

        response = self.client.get(
            reverse('user_page', args = ('user',)) + "?sub=uploaded")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(
            response.content.find("IMAGE2") < response.content.find("IMAGE1"), True)

        image1.delete()
        image2.delete()

        # Test "acquisition time" sorting
        image1 = Image.objects.create(user = self.user, title = "IMAGE1")
        image2 = Image.objects.create(user = self.user, title = "IMAGE2")
        acquisition1 = Acquisition.objects.create(image = image1, date = today)
        acquisition2 = Acquisition.objects.create(

            image = image2, date = today + timedelta(1))
        response = self.client.get(
            reverse('user_page', args = ('user',)) + "?sub=acquired")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(
            response.content.find("IMAGE2") < response.content.find("IMAGE1"), True)

        acquisition1.delete()
        acquisition2.delete()
        image1.delete()
        image2.delete()

        # Test "subject type" sub-section
        image1 = Image.objects.create(user = self.user, title = "IMAGE1_DEEP", subject_type = 100)
        image2 = Image.objects.create(user = self.user, title = "IMAGE2_SOLAR", subject_type = 200)
        image3 = Image.objects.create(user = self.user, title = "IMAGE3_WIDE", subject_type = 300)
        image4 = Image.objects.create(user = self.user, title = "IMAGE4_TRAILS", subject_type = 400)
        image5 = Image.objects.create(user = self.user, title = "IMAGE5_GEAR", subject_type = 500)
        image6 = Image.objects.create(user = self.user, title = "IMAGE6_OTHER", subject_type = 600)

        response = self.client.get(reverse('user_page', args = ('user',)) + "?sub=subject")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, True)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, False)
        self.assertEquals(image4.title in response.content, False)
        self.assertEquals(image5.title in response.content, False)
        self.assertEquals(image6.title in response.content, False)

        response = self.client.get(reverse('user_page', args = ('user',)) + "?sub=subject&active=DEEP")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, True)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, False)
        self.assertEquals(image4.title in response.content, False)
        self.assertEquals(image5.title in response.content, False)
        self.assertEquals(image6.title in response.content, False)

        response = self.client.get(reverse('user_page', args = ('user',)) + "?sub=subject&active=SOLAR")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, False)
        self.assertEquals(image2.title in response.content, True)
        self.assertEquals(image3.title in response.content, False)
        self.assertEquals(image4.title in response.content, False)
        self.assertEquals(image5.title in response.content, False)
        self.assertEquals(image6.title in response.content, False)

        response = self.client.get(reverse('user_page', args = ('user',)) + "?sub=subject&active=WIDE")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, False)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, True)
        self.assertEquals(image4.title in response.content, False)
        self.assertEquals(image5.title in response.content, False)
        self.assertEquals(image6.title in response.content, False)

        response = self.client.get(reverse('user_page', args = ('user',)) + "?sub=subject&active=TRAILS")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, False)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, False)
        self.assertEquals(image4.title in response.content, True)
        self.assertEquals(image5.title in response.content, False)
        self.assertEquals(image6.title in response.content, False)

        response = self.client.get(reverse('user_page', args = ('user',)) + "?sub=subject&active=GEAR")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, False)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, False)
        self.assertEquals(image4.title in response.content, False)
        self.assertEquals(image5.title in response.content, True)
        self.assertEquals(image6.title in response.content, False)

        response = self.client.get(reverse('user_page', args = ('user',)) + "?sub=subject&active=OTHER")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, False)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, False)
        self.assertEquals(image4.title in response.content, False)
        self.assertEquals(image5.title in response.content, False)
        self.assertEquals(image6.title in response.content, True)

        image1.delete()
        image2.delete()
        image3.delete()
        image4.delete()
        image5.delete()
        image6.delete()

        # Test "year" sub-section
        image1 = Image.objects.create(user = self.user, title = "IMAGE1")
        image2 = Image.objects.create(user = self.user, title = "IMAGE2")
        image3 = Image.objects.create(user = self.user, title = "IMAGE3")
        acquisition1 = Acquisition.objects.create(image = image1, date = today)
        acquisition2 = Acquisition.objects.create(
            image = image2, date = today - timedelta(365))

        response = self.client.get(
            reverse('user_page', args = ('user',)) + "?sub=year")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, True)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, False)

        response = self.client.get(
            reverse('user_page', args = ('user',)) + "?sub=year&active=%d" % today.year)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, True)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, False)

        response = self.client.get(
            reverse('user_page', args = ('user',)) + "?sub=year&active=%d" % (today.year - 1))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, False)
        self.assertEquals(image2.title in response.content, True)
        self.assertEquals(image3.title in response.content, False)

        response = self.client.get(
            reverse('user_page', args = ('user',)) + "?sub=year&active=0")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, False)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, True)

        acquisition1.delete()
        acquisition2.delete()
        image1.delete()
        image2.delete()
        image3.delete()

        # Test "gear" sub-section
        image1 = Image.objects.create(user = self.user, title = "IMAGE1")
        image2 = Image.objects.create(user = self.user, title = "IMAGE2")
        image3 = Image.objects.create(user = self.user, title = "IMAGE3", subject_type = 200)
        image4 = Image.objects.create(user = self.user, title = "IMAGE4", subject_type = 500)

        telescope1 = Telescope.objects.create(name = "TELESCOPE1")
        telescope2 = Telescope.objects.create(name = "TELESCOPE2")
        image1.imaging_telescopes.add(telescope1)
        image1.save()
        image2.imaging_telescopes.add(telescope2)
        image2.save()

        response = self.client.get(
            reverse('user_page', args = ('user',)) + "?sub=gear&active=%d" % telescope1.pk)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, True)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, False)
        self.assertEquals(image4.title in response.content, False)

        response = self.client.get(
            reverse('user_page', args = ('user',)) + "?sub=gear&active=%d" % telescope2.pk)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, False)
        self.assertEquals(image2.title in response.content, True)
        self.assertEquals(image3.title in response.content, False)
        self.assertEquals(image4.title in response.content, False)

        response = self.client.get(
            reverse('user_page', args = ('user',)) + "?sub=gear&active=0")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, False)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, True)
        self.assertEquals(image4.title in response.content, False)

        response = self.client.get(
            reverse('user_page', args = ('user',)) + "?sub=gear&active=-1")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image1.title in response.content, False)
        self.assertEquals(image2.title in response.content, False)
        self.assertEquals(image3.title in response.content, False)
        self.assertEquals(image4.title in response.content, True)

        telescope1.delete()
        telescope2.delete()
        image1.delete()
        image2.delete()
        image3.delete()
        image4.delete()

        # Test "no data" sub-section
        image = Image.objects.create(user = self.user, title = "IMAGE_NODATA")

        image.subject_type = 100
        image.objects_in_field = None
        image.save()
        response = self.client.get(
            reverse('user_page', args = ('user',)) + "?sub=nodata")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image.title in response.content, True)

        image.subject_type = 200
        image.solar_system_main_subject = None
        image.save()
        response = self.client.get(
            reverse('user_page', args = ('user',)) + "?sub=nodata")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image.title in response.content, True)

        response = self.client.get(
            reverse('user_page', args = ('user',)) + "?sub=nodata&active=GEAR")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image.title in response.content, True)

        response = self.client.get(
            reverse('user_page', args = ('user',)) + "?sub=nodata&active=ACQ")
        self.assertEquals(response.status_code, 200)
        self.assertEquals(image.title in response.content, True)

        image.delete()
