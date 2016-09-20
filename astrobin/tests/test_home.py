# Django
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase


class HomeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test', 'test@test.com', 'password')

    def tearDown(self):
        self.user.delete()

    def test_default_section_view(self):
        def url(section):
            return reverse('set_default_frontpage_section', args = (section,))

        self.client.login(username = 'test', password = 'password')

        response = self.client.get(reverse('index'))
        self.assertContains(response, '<h4><i class="icon-group"></i><span class="hidden-phone">Your activity stream</span></h4>', html = True)

        response = self.client.post(url('global'), follow = True)
        self.assertContains(response, '<h4><i class="icon-globe"></i><span class="hidden-phone">Global activity stream</span></h4>', html = True)

        response = self.client.post(url('images'), follow = True)
        self.assertContains(response, '<h4><i class="icon-time"></i><span class="hidden-phone">Recently uploaded</span></h4>', html = True)

        response = self.client.post(url('followed'), follow = True)
        self.assertContains(response, '<h4><i class="icon-eye-open"></i><span class="hidden-phone">Recent images from people you follow</span></h4>', html = True)

        # Following two are unsupported with sqlite

        #response = self.client.post(url('liked'), follow = True)
        #self.assertContains(response, '<h4><i class="icon-thumbs-up"></i><span class="hidden-phone">Recently liked</span></h4>', html = True)

        #response = self.client.post(url('bookmarked'), follow = True)
        #self.assertContains(response, '<h4><i class="icon-bookmark"></i><span class="hidden-phone">Recently bookmarked</span></h4>', html = True)

        response = self.client.post(url('fits'), follow = True)
        self.assertContains(response, '<h4><i class="icon-archive"></i><span class="hidden-phone">Recent images with link to TIFF/FITS</span></h4>', html = True)

        self.client.logout()
