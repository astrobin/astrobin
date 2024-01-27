from datetime import datetime

from django.test import TestCase
from mock.mock import patch

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

    def test_string_to_date_valid_date_str(self):
        """ Test with valid date strings. """
        date_str = "2023-01-01"
        expected_date = datetime(2023, 1, 1)
        self.assertEqual(DateTimeService.string_to_date(date_str), expected_date)

    def test_string_to_date_invalid_date_str(self):
        """ Test with invalid date strings. """
        invalid_date_str = "2023-02-30"
        with self.assertRaises(ValueError):
            DateTimeService.string_to_date(invalid_date_str)

    def test_format_date_range_same_month_valid_same_month_range(self):
        """ Test with valid date range within the same month. """
        start_str = "2023-01-10"
        end_str = "2023-01-15"
        expected_output = "Jan. 10 - 15, 2023"
        self.assertEqual(
            DateTimeService.format_date_range_same_month(start_str, end_str, 'en'),
            expected_output
        )

    def test_format_date_range_same_month_not_same_month(self):
        """ Test with invalid date range (not the same monty). """
        start_str = "2023-01-20"
        end_str = "2023-02-10"
        with self.assertRaises(ValueError):
            DateTimeService.format_date_range_same_month(start_str, end_str, 'en')

    def test_format_date_range_same_month_not_same_year(self):
        """ Test with invalid date range (not the same year). """
        start_str = "2023-01-20"
        end_str = "2024-01-10"
        with self.assertRaises(ValueError):
            DateTimeService.format_date_range_same_month(start_str, end_str, 'en')

    def test_format_date_range_same_month_invalid_date_range(self):
        """ Test with invalid date range (like end date before start date). """
        start_str = "2023-01-20"
        end_str = "2023-01-10"
        with self.assertRaises(ValueError):
            DateTimeService.format_date_range_same_month(start_str, end_str, 'en')

    def test_format_date_range_same_year_valid_same_year_range(self):
        """ Test with valid date range within the same year. """
        start_str = "2023-01-10"
        end_str = "2023-03-15"
        expected_output = "Jan. 10 - March 15, 2023"  # Only long month names are shortened
        self.assertEqual(
            DateTimeService.format_date_range_same_year(start_str, end_str, 'en'),
            expected_output
        )

    def test_format_date_range_same_year_not_same_year(self):
        """ Test with invalid date range (not the same year). """
        start_str = "2023-01-10"
        end_str = "2024-03-15"
        with self.assertRaises(ValueError):
            DateTimeService.format_date_range_same_year(start_str, end_str, 'en')

    def test_format_date_range_same_year_invalid_date_range(self):
        """ Test with invalid date range (end date before start date). """
        start_str = "2023-03-20"
        end_str = "2023-01-10"
        with self.assertRaises(ValueError):
            DateTimeService.format_date_range_same_year(start_str, end_str, 'en')

    def test_format_date_range_different_year_valid_different_year_range(self):
        """ Test with invalid date range (not a different year). """
        start_str = "2022-12-25"
        end_str = "2023-01-05"
        expected_output = "Dec. 25, 2022 - Jan. 5, 2023"
        self.assertEqual(
            DateTimeService.format_date_range_different_year(start_str, end_str, 'en'),
            expected_output
        )

    def test_format_date_range_different_year_same_year(self):
        """ Test same year. """
        start_str = "2023-01-01"
        end_str = "2023-12-31"
        with self.assertRaises(ValueError):
            DateTimeService.format_date_range_different_year(start_str, end_str, 'en')

    def test_format_date_range_different_year_invalid_date_range(self):
        """ Test with invalid date range (end date before start date). """
        start_str = "2023-01-01"
        end_str = "2022-12-31"
        with self.assertRaises(ValueError):
            DateTimeService.format_date_range_different_year(start_str, end_str, 'en')

    def test_format_date_with_valid_data(self):
        """ Test formatting of date with valid inputs. """
        date_str = "2023-04-01"
        expected_output = "April 1, 2023"
        self.assertEqual(
            DateTimeService.format_date(date_str, 'en'),
            expected_output
        )

    def test_format_date_with_invalid_data(self):
        """ Test formatting of date with invalid inputs. """
        invalid_date_str = "2023-04-31"  # Invalid date
        with self.assertRaises(ValueError):
            DateTimeService.format_date(invalid_date_str, 'en')

    @patch('common.services.DateTimeService.format_date')
    def test_format_date_range_same_day_range_calls_format_date(self, mock_format_date):
        start_str = end_str = "2023-01-01"
        language_code = 'en'
        DateTimeService.format_date_range(start_str, end_str, language_code)
        mock_format_date.assert_called_once_with(start_str, language_code)

    @patch('common.services.DateTimeService.format_date_range_same_month')
    def test_format_date_range_same_month_range_calls_format_date_range_same_month(self, mock_format_same_month):
        start_str = "2023-01-10"
        end_str = "2023-01-15"
        language_code = 'en'
        DateTimeService.format_date_range(start_str, end_str, language_code)
        mock_format_same_month.assert_called_once_with(start_str, end_str, language_code)

    @patch('common.services.DateTimeService.format_date_range_same_year')
    def test_format_date_range_same_year_range_calls_format_date_range_same_year(self, mock_format_same_year):
        start_str = "2023-01-01"
        end_str = "2023-02-01"
        language_code = 'en'
        DateTimeService.format_date_range(start_str, end_str, language_code)
        mock_format_same_year.assert_called_once_with(start_str, end_str, language_code)

    @patch('common.services.DateTimeService.format_date_range_different_year')
    def test_format_date_range_different_year_range_calls_format_date_range_different_year(self, mock_format_different_year):
        start_str = "2022-12-31"
        end_str = "2023-01-01"
        language_code = 'en'
        DateTimeService.format_date_range(start_str, end_str, language_code)
        mock_format_different_year.assert_called_once_with(start_str, end_str, language_code)

    @patch('common.services.DateTimeService.format_date')
    @patch('common.services.DateTimeService.format_date_range')
    def test_split_date_ranges(self, mock_format_date_range, mock_format_date):
        date_ranges_str = "2023-01-01, 2023-01-10 - 2023-01-15"
        language_code = 'en'

        components = DateTimeService.split_date_ranges(date_ranges_str, language_code)

        # Check the first component (single date)
        self.assertEqual(components[0]['date'], mock_format_date.return_value)
        self.assertEqual(components[0]['start'], "2023-01-01")
        self.assertEqual(components[0]['end'], "2023-01-01")
        mock_format_date.assert_called_once_with("2023-01-01", language_code)

        # Check the second component (date range)
        self.assertEqual(components[1]['range'], mock_format_date_range.return_value)
        self.assertEqual(components[1]['start'], "2023-01-10")
        self.assertEqual(components[1]['end'], "2023-01-15")
        mock_format_date_range.assert_called_once_with("2023-01-10", "2023-01-15", language_code)
