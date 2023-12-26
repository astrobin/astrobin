from django.test import TestCase

from common.services import DateTimeService


class DateTimeServiceTest(TestCase):
    def test_human_time_duration(self):
        self.assertEqual('0&Prime;', DateTimeService.human_time_duration(None))
        self.assertEqual('0&Prime;', DateTimeService.human_time_duration(0))
        self.assertEqual('1&prime;', DateTimeService.human_time_duration(60))
        self.assertEqual('1h', DateTimeService.human_time_duration(60 * 60))
        self.assertEqual('10h', DateTimeService.human_time_duration(60 * 60 * 10))
        self.assertEqual('1h 1&prime;', DateTimeService.human_time_duration(60 * 60 + 60))
        self.assertEqual('1h 1&prime; 1&Prime;', DateTimeService.human_time_duration(60 * 60 + 60 + 1))
        self.assertEqual('1h 1&prime; 1&Prime; .1', DateTimeService.human_time_duration(60 * 60 + 60 + 1.1))
        self.assertEqual('25h', DateTimeService.human_time_duration(25 * 60 * 60))
        self.assertEqual('0.25&Prime;', DateTimeService.human_time_duration(.25))

    def test_format_date_ranges_sequence_of_contiguous_and_non_contiguous_dates(self):
        self.assertEqual(
            DateTimeService.format_date_ranges(['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-05', '2023-01-07']),
            '2023-01-01 - 2023-01-03, 2023-01-05, 2023-01-07'
        )

    def test_format_date_ranges_only_contiguous_dates(self):
        self.assertEqual(
            DateTimeService.format_date_ranges(['2023-01-01', '2023-01-02', '2023-01-03']),
            '2023-01-01 - 2023-01-03'
        )

    def test_format_date_ranges_only_non_contiguous_dates(self):
        self.assertEqual(
            DateTimeService.format_date_ranges(['2023-01-01', '2023-01-03', '2023-01-05']),
            '2023-01-01, 2023-01-03, 2023-01-05'
        )

    def test_format_date_ranges_single_date(self):
        self.assertEqual(
            DateTimeService.format_date_ranges(['2023-01-01']),
            '2023-01-01'
        )

    def test_format_date_ranges_no_dates(self):
        self.assertEqual(
            DateTimeService.format_date_ranges([]),
            ''
        )

    def test_format_date_ranges_unsorted_dates(self):
        self.assertEqual(
            DateTimeService.format_date_ranges(['2023-01-05', '2023-01-01', '2023-01-03', '2023-01-02', '2023-01-04']),
            '2023-01-01 - 2023-01-05'
        )

    def test_format_date_ranges_duplicate_dates(self):
        self.assertEqual(
            DateTimeService.format_date_ranges(['2023-01-01', '2023-01-01', '2023-01-02']),
            '2023-01-01 - 2023-01-02'
        )
