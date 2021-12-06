from datetime import datetime

from django.test import TestCase
from mock import patch

from astrobin.services.utils_service import UtilsService


class UtilsServiceTest(TestCase):
    @patch('common.services.DateTimeService.today')
    def test_show_10_year_anniversary_logo_too_early(self, today):
        today.return_value = datetime(2019, 11, 27).date()
        self.assertFalse(UtilsService.show_10_year_anniversary_logo())

        today.return_value = datetime(2020, 11, 26).date()
        self.assertFalse(UtilsService.show_10_year_anniversary_logo())

        today.return_value = datetime(2021, 11, 26).date()
        self.assertFalse(UtilsService.show_10_year_anniversary_logo())

    @patch('common.services.DateTimeService.today')
    def test_show_10_year_anniversary_logo_too_late(self, today):
        today.return_value = datetime(2020, 12, 4).date()
        self.assertFalse(UtilsService.show_10_year_anniversary_logo())

        today.return_value = datetime(2021, 12, 4).date()
        self.assertFalse(UtilsService.show_10_year_anniversary_logo())

        today.return_value = datetime(2022, 11, 27).date()
        self.assertFalse(UtilsService.show_10_year_anniversary_logo())

    @patch('common.services.DateTimeService.today')
    def test_show_10_year_anniversary_logo_right_time_code_anniversary(self, today):
        today.return_value = datetime(2020, 11, 27).date()
        self.assertTrue(UtilsService.show_10_year_anniversary_logo())

        today.return_value = datetime(2020, 11, 28).date()
        self.assertFalse(UtilsService.show_10_year_anniversary_logo())

    @patch('common.services.DateTimeService.today')
    def test_show_10_year_anniversary_logo_right_time_publication_anniversary(self, today):
        today.return_value = datetime(2021, 11, 27).date()
        self.assertTrue(UtilsService.show_10_year_anniversary_logo())

        today.return_value = datetime(2021, 11, 28).date()
        self.assertFalse(UtilsService.show_10_year_anniversary_logo())

    def test_unique(self):
        self.assertEqual([], UtilsService.unique([]))
        self.assertEqual([1], UtilsService.unique([1]))
        self.assertEqual([1], UtilsService.unique([1, 1]))
        self.assertEqual([1, 2], UtilsService.unique([1, 2]))
        self.assertEqual([1, 2], UtilsService.unique([1, 2, 1]))
        self.assertEqual([2, 1], UtilsService.unique([2, 1, 2]))
