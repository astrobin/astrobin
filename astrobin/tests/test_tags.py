# -*- coding: utf-8 -*-

import datetime

from django.test import TestCase

from astrobin.templatetags.tags import date_before, ra_to_hms, dec_to_dms


class TagsTest(TestCase):
    def test_date_before(self):
        d1 = datetime.datetime.now()
        d2 = d1 - datetime.timedelta(days=1)

        self.assertTrue(date_before(d2, d1))

        d2 = d1

        self.assertFalse(date_before(d2, d1))

        d2 = d1 + datetime.timedelta(days=1)

        self.assertFalse(date_before(d2, d1))

    def test_ra_to_hms(self):
        self.assertEqual('03<span class="symbol">h</span>22<span class="symbol">m</span>00<span class="symbol">s</span>', ra_to_hms(50.5))
        self.assertEqual('-03<span class="symbol">h</span>22<span class="symbol">m</span>00<span class="symbol">s</span>', ra_to_hms(-50.5))
        self.assertEqual('10<span class="symbol">h</span>20<span class="symbol">m</span>15<span class="symbol">s</span>', ra_to_hms(155.0625 ))
        self.assertEqual('00<span class="symbol">h</span>00<span class="symbol">m</span>00<span class="symbol">s</span>', ra_to_hms(0))

    def test_ra_to_hms_with_precision_3(self):
        self.assertEqual('03<span class="symbol">h</span>22<span class="symbol">m</span>00<span class="symbol">s</span>.000', ra_to_hms(50.5, precision=3))
        self.assertEqual('03<span class="symbol">h</span>22<span class="symbol">m</span>02<span class="symbol">s</span>.400', ra_to_hms(50.51, precision=3))
        self.assertEqual('-03<span class="symbol">h</span>22<span class="symbol">m</span>00<span class="symbol">s</span>.000', ra_to_hms(-50.5, precision=3))
        self.assertEqual('-03<span class="symbol">h</span>22<span class="symbol">m</span>02<span class="symbol">s</span>.400', ra_to_hms(-50.51, precision=3))
        self.assertEqual('10<span class="symbol">h</span>20<span class="symbol">m</span>15<span class="symbol">s</span>.000', ra_to_hms(155.0625, precision=3))
        self.assertEqual('10<span class="symbol">h</span>20<span class="symbol">m</span>15<span class="symbol">s</span>.120', ra_to_hms(155.06255, precision=3))
        self.assertEqual('00<span class="symbol">h</span>00<span class="symbol">m</span>24<span class="symbol">s</span>.000', ra_to_hms(0.1, precision=3))
        self.assertEqual('00<span class="symbol">h</span>00<span class="symbol">m</span>00<span class="symbol">s</span>.000', ra_to_hms(0, precision=3))

    def test_dec_to_dms(self):
        self.assertEqual('+50<span class="symbol">°</span>30<span class="symbol">′</span>00<span class="symbol">″</span>', dec_to_dms(50.5))
        self.assertEqual('-50<span class="symbol">°</span>30<span class="symbol">′</span>00<span class="symbol">″</span>', dec_to_dms(-50.5))
        self.assertEqual('+00<span class="symbol">°</span>00<span class="symbol">′</span>00<span class="symbol">″</span>', dec_to_dms(0))

    def test_dec_to_dms_with_precision_2(self):
        self.assertEqual('+50<span class="symbol">°</span>30<span class="symbol">′</span>00<span class="symbol">″</span>.00', dec_to_dms(50.5, precision=2))
        self.assertEqual('+50<span class="symbol">°</span>30<span class="symbol">′</span>36<span class="symbol">″</span>.00', dec_to_dms(50.51, precision=2))
        self.assertEqual('-50<span class="symbol">°</span>30<span class="symbol">′</span>00<span class="symbol">″</span>.00', dec_to_dms(-50.5, precision=2))
        self.assertEqual('-50<span class="symbol">°</span>30<span class="symbol">′</span>36<span class="symbol">″</span>.00', dec_to_dms(-50.51, precision=2))
        self.assertEqual('+00<span class="symbol">°</span>06<span class="symbol">′</span>00<span class="symbol">″</span>.00', dec_to_dms(0.1, precision=2))
        self.assertEqual('+00<span class="symbol">°</span>00<span class="symbol">′</span>00<span class="symbol">″</span>.00', dec_to_dms(0, precision=2))
