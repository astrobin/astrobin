from django.core.urlresolvers import reverse_lazy
from django.test import TestCase


class SpecialViewsTest(TestCase):
    def test_ads_txt_ok(self):
        with self.settings(ADSENSE_PUBLISHER_ID="foobar", ADSENSE_ENABLED=True):
            response = self.client.get(reverse_lazy('ads_txt'))
            self.assertEquals(response.status_code, 200)
            self.assertContains(response, "google.com, pub-foobar, DIRECT, f08c47fec0942fa0")

    def test_ads_txt_404(self):
        with self.settings(ADSENSE_PUBLISHER_ID=None, ADSENSE_ENABLED=True):
            response = self.client.get(reverse_lazy('ads_txt'))
            self.assertEquals(response.status_code, 404)
