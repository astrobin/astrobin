from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, RequestFactory

from astrobin.models import Image
from astrobin_apps_images.templatetags.astrobin_apps_images_tags import astrobin_image


class TagTests(TestCase):
    def test_astrobin_image_tag_uses_hashed_url(self):
        request = RequestFactory().get("/")
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()

        context = {
            "request": request
        }

        image = Image.objects.create(
            user=User.objects.create(
                username="test",
                email="test@test.com",
                password="test",
            ),
            image_file=SimpleUploadedFile(
                name='test.jpg',
                content=open("astrobin/fixtures/test.jpg", 'rb').read(),
                content_type='image/jpeg')

        )
        image.save()
        result = astrobin_image(context, image, "regular")

        self.assertEquals("/%s/" % image.hash, result["url"])
