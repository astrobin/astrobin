from datetime import datetime

from django.test import TestCase
from mock import patch

from astrobin.services.utils_service import UtilsService


class UtilsServiceTest(TestCase):
    def test_unique(self):
        self.assertEqual([], UtilsService.unique([]))
        self.assertEqual([1], UtilsService.unique([1]))
        self.assertEqual([1], UtilsService.unique([1, 1]))
        self.assertEqual([1, 2], UtilsService.unique([1, 2]))
        self.assertEqual([1, 2], UtilsService.unique([1, 2, 1]))
        self.assertEqual([2, 1], UtilsService.unique([2, 1, 2]))

    def test_split_text_alphanumerically(self):
        self.assertEqual([], UtilsService.split_text_alphanumerically(''))
        self.assertEqual(['a'], UtilsService.split_text_alphanumerically('a'))
        self.assertEqual(['a', '1'], UtilsService.split_text_alphanumerically('a1'))
        self.assertEqual(['a', '1', 'b'], UtilsService.split_text_alphanumerically('a1b'))
        self.assertEqual(['a', '1', 'b'], UtilsService.split_text_alphanumerically('a 1 b'))
