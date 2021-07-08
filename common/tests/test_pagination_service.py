from django.test import TestCase

from common.services.pagination_service import PaginationService


class PaginationServiceTest(TestCase):
    def test_page_counter(self):
        self.assertEqual(1, PaginationService.page_counter(1, 1, 100))
        self.assertEqual(100, PaginationService.page_counter(100, 1, 100))
        self.assertEqual(101, PaginationService.page_counter(1, 2, 100))
