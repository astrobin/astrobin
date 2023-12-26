# -*- coding: utf-8 -*-

import datetime

from django.template import Context, Template
from django.test import TestCase
from django.utils.html import escape

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
        self.assertEqual('03<span class="symbol">h</span>22<span class="symbol">m</span>00<span class="symbol">s</span>.0', ra_to_hms(50.5))
        self.assertEqual('-03<span class="symbol">h</span>22<span class="symbol">m</span>00<span class="symbol">s</span>.0', ra_to_hms(-50.5))
        self.assertEqual('10<span class="symbol">h</span>20<span class="symbol">m</span>15<span class="symbol">s</span>.0', ra_to_hms(155.0625 ))
        self.assertEqual('00<span class="symbol">h</span>00<span class="symbol">m</span>00<span class="symbol">s</span>.0', ra_to_hms(0))

    def test_ra_to_hms_with_small_pixel_scale(self):
        self.assertEqual('03<span class="symbol">h</span>22<span class="symbol">m</span>00<span class="symbol">s</span>.000', ra_to_hms(50.5, pixel_scale=.1))
        self.assertEqual('03<span class="symbol">h</span>22<span class="symbol">m</span>02<span class="symbol">s</span>.400', ra_to_hms(50.51, pixel_scale=.1))
        self.assertEqual('-03<span class="symbol">h</span>22<span class="symbol">m</span>00<span class="symbol">s</span>.000', ra_to_hms(-50.5, pixel_scale=.1))
        self.assertEqual('-03<span class="symbol">h</span>22<span class="symbol">m</span>02<span class="symbol">s</span>.400', ra_to_hms(-50.51, pixel_scale=.1))
        self.assertEqual('10<span class="symbol">h</span>20<span class="symbol">m</span>15<span class="symbol">s</span>.000', ra_to_hms(155.0625, pixel_scale=.1))
        self.assertEqual('10<span class="symbol">h</span>20<span class="symbol">m</span>15<span class="symbol">s</span>.120', ra_to_hms(155.06255, pixel_scale=.1))
        self.assertEqual('00<span class="symbol">h</span>00<span class="symbol">m</span>24<span class="symbol">s</span>.000', ra_to_hms(0.1, pixel_scale=.1))
        self.assertEqual('00<span class="symbol">h</span>00<span class="symbol">m</span>00<span class="symbol">s</span>.000', ra_to_hms(0, pixel_scale=.1))

    def test_dec_to_dms(self):
        self.assertEqual('+50<span class="symbol">°</span>30<span class="symbol">′</span>00<span class="symbol">″</span>', dec_to_dms(50.5))
        self.assertEqual('-50<span class="symbol">°</span>30<span class="symbol">′</span>00<span class="symbol">″</span>', dec_to_dms(-50.5))
        self.assertEqual('+00<span class="symbol">°</span>00<span class="symbol">′</span>00<span class="symbol">″</span>', dec_to_dms(0))

    def test_dec_to_dms_with_small_pixel_scale(self):
        self.assertEqual('+50<span class="symbol">°</span>30<span class="symbol">′</span>00<span class="symbol">″</span>.00', dec_to_dms(50.5, pixel_scale=.1))
        self.assertEqual('+50<span class="symbol">°</span>30<span class="symbol">′</span>36<span class="symbol">″</span>.00', dec_to_dms(50.51, pixel_scale=.1))
        self.assertEqual('-50<span class="symbol">°</span>30<span class="symbol">′</span>00<span class="symbol">″</span>.00', dec_to_dms(-50.5, pixel_scale=.1))
        self.assertEqual('-50<span class="symbol">°</span>30<span class="symbol">′</span>36<span class="symbol">″</span>.00', dec_to_dms(-50.51, pixel_scale=.1))
        self.assertEqual('+00<span class="symbol">°</span>06<span class="symbol">′</span>00<span class="symbol">″</span>.00', dec_to_dms(0.1, pixel_scale=.1))
        self.assertEqual('+00<span class="symbol">°</span>00<span class="symbol">′</span>00<span class="symbol">″</span>.00', dec_to_dms(0, pixel_scale=.1))

    def test_same_month_range(self):
        template = Template("{% load tags %}{{ '2023-01-01 - 2023-01-05'|split_date_ranges }}")
        expected_output = escape("[{'range': 'Jan 1-5, 2023', 'start': '2023-01-01', 'end': '2023-01-05'}]")
        self.assertEqual(template.render(Context({})), expected_output)

    def test_cross_month_range(self):
        template = Template("{% load tags %}{{ '2023-01-30 - 2023-02-02'|split_date_ranges }}")
        expected_output = escape("[{'range': 'Jan 30 - Feb 2, 2023', 'start': '2023-01-30', 'end': '2023-02-02'}]")
        self.assertEqual(template.render(Context({})), expected_output)

    def test_cross_year_range(self):
        template = Template("{% load tags %}{{ '2023-12-30 - 2024-01-02'|split_date_ranges }}")
        expected_output = escape(
            "[{'range': 'Dec 30, 2023 - Jan 2, 2024', 'start': '2023-12-30', 'end': '2024-01-02'}]"
        )
        self.assertEqual(template.render(Context({})), expected_output)

    def test_single_date_range(self):
        template = Template("{% load tags %}{{ '2023-01-01 - 2023-01-01'|split_date_ranges }}")
        expected_output = escape("[{'range': 'Jan 1, 2023', 'start': '2023-01-01', 'end': '2023-01-01'}]")
        self.assertEqual(template.render(Context({})), expected_output)

    def test_multiple_ranges(self):
        template = Template(
            "{% load tags %}{{ '2023-01-01 - 2023-01-03, 2023-02-01 - 2023-02-05'|split_date_ranges }}"
        )
        expected_output = escape(
            "[{'range': 'Jan 1-3, 2023', 'start': '2023-01-01', 'end': '2023-01-03'}, "
            "{'range': 'Feb 1-5, 2023', 'start': '2023-02-01', 'end': '2023-02-05'}]"
        )
        self.assertEqual(template.render(Context({})), expected_output)

    def test_edge_case_empty_string(self):
        template = Template("{% load tags %}{{ ''|split_date_ranges }}")
        self.assertEqual(template.render(Context({})), "[]")

    def test_invalid_date_format(self):
        template = Template("{% load tags %}{{ 'invalid-date'|split_date_ranges }}")
        self.assertRaises(ValueError, template.render, Context({}))
