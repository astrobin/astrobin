from django.test import TestCase

from common.services.pagination_service import PaginationService


class PaginationServiceTest(TestCase):
    def test_page_counter(self):
        self.assertEquals(1, PaginationService.page_counter(1, 1, 100))
        self.assertEquals(100, PaginationService.page_counter(100, 1, 100))
        self.assertEquals(101, PaginationService.page_counter(1, 2, 100))
