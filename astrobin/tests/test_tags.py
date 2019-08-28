import datetime

from django.test import TestCase

from astrobin.templatetags.tags import date_before


class TagsTest(TestCase):
    def test_date_before(self):
        d1 = datetime.datetime.now()
        d2 = d1 - datetime.timedelta(days=1)

        self.assertTrue(date_before(d2, d1))

        d2 = d1

        self.assertFalse(date_before(d2, d1))

        d2 = d1 + datetime.timedelta(days=1)

        self.assertFalse(date_before(d2, d1))
