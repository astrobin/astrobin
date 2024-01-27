import time
from datetime import datetime, date, timedelta

from django.conf import settings
from django.utils.formats import date_format


class DateTimeService:
    @staticmethod
    def today():
        # type: () -> date
        return date.today()

    @staticmethod
    def now():
        # type: () -> datetime
        return datetime.now()

    @staticmethod
    def next_midnight(dt=datetime.now()):
        # type: (datetime) -> datetime
        return datetime.combine(date(dt.year, dt.month, dt.day) + timedelta(1), datetime.min.time())

    @staticmethod
    def epoch(dt=datetime.now()):
        try:
            return int(time.mktime(dt.timetuple()) * 1000)
        except AttributeError:
            return ''

    @staticmethod
    def human_time_duration(seconds, html=True):
        prime_symbol = '&prime;' if html else '\''
        double_prime_symbol = '&Prime;' if html else '"'

        if seconds is None or seconds == 0:
            return f'0{double_prime_symbol}'

        if seconds < 1:
            return '{:.4f}'.format(seconds).rstrip('0').rstrip('.') + double_prime_symbol

        hours, reminder = divmod(seconds, 60 * 60)
        minutes, reminder = divmod(reminder, 60)
        seconds, reminder = divmod(reminder, 1)

        parts = []

        if hours > 0:
            parts.append('{}{}'.format(int(hours), 'h'))

        if minutes > 0:
            parts.append('{}{}'.format(int(minutes), prime_symbol))

        if seconds > 0:
            parts.append('{}{}'.format(int(seconds), double_prime_symbol))

        if reminder > 0:
            parts.append('{:.4f}'.format(reminder).replace('0.', '.').rstrip('0').rstrip('.'))

        return ' '.join(parts)

    @staticmethod
    def format_date_ranges(dates, format_func=lambda d: d.strftime("%Y-%m-%d")):
        """Formats a list of dates into a string representing contiguous date ranges and individual dates."""
        if not dates:
            return ""

        # Convert dates to datetime objects for easier manipulation
        # Handles both string and datetime.date inputs
        sorted_dates = sorted(
            set(
                datetime.strptime(d, "%Y-%m-%d")
                if isinstance(d, str)
                else datetime.combine(d, datetime.min.time())
                for d in dates
            )
        )

        # Initialize variables
        formatted_ranges = []
        start_date = end_date = sorted_dates[0]

        for d in sorted_dates[1:]:
            if d == end_date + timedelta(days=1):
                end_date = d
            else:
                if start_date == end_date:
                    formatted_ranges.append(format_func(start_date))
                else:
                    formatted_ranges.append(f"{format_func(start_date)} - {format_func(end_date)}")
                start_date = end_date = d

        # Add the last range or single date
        if start_date == end_date:
            formatted_ranges.append(format_func(start_date))
        else:
            formatted_ranges.append(f"{format_func(start_date)} - {format_func(end_date)}")

        return ", ".join(formatted_ranges)

    @staticmethod
    def string_to_date(date_str: str) -> datetime:
        return datetime.strptime(date_str, "%Y-%m-%d")

    @staticmethod
    def format_date_range_same_month(start_str: str, end_str: str, language_code: str) -> str:
        start_date = DateTimeService.string_to_date(start_str)
        end_date = DateTimeService.string_to_date(end_str)

        if start_date >= end_date:
            raise ValueError("End date must be greater than start date.")

        if start_date.year != end_date.year:
            raise ValueError("Start date and end date must be in the same year.")

        if start_date.month != end_date.month:
            raise ValueError("Start date and end date must be in the same month.")

        fmt = settings.ALL_DATE_FORMATS[language_code]

        day1 = date_format(start_date, fmt['DAY'])
        day2 = date_format(end_date, fmt['DAY'])
        month = date_format(start_date, fmt['MONTH'])
        year = date_format(end_date, fmt['YEAR'])

        return fmt['RANGE_SAME_MONTH'] \
            .replace(f'{fmt["DAY"]}1', day1) \
            .replace(f'{fmt["DAY"]}2', day2) \
            .replace(f'{fmt["MONTH"]}', month) \
            .replace(f'{fmt["YEAR"]}', year)

    @staticmethod
    def format_date_range_same_year(start_str: str, end_str: str, language_code: str) -> str:
        start_date = DateTimeService.string_to_date(start_str)
        end_date = DateTimeService.string_to_date(end_str)

        if start_date >= end_date:
            raise ValueError("End date must be greater than start date.")

        if start_date.year != end_date.year:
            raise ValueError("Start date and end date must be in the same year.")

        fmt = settings.ALL_DATE_FORMATS[language_code]

        day1 = date_format(start_date, fmt['DAY'])
        day2 = date_format(end_date, fmt['DAY'])
        month1 = date_format(start_date, fmt['MONTH'])
        month2 = date_format(end_date, fmt['MONTH'])
        year = date_format(end_date, fmt['YEAR'])

        return fmt['RANGE_SAME_YEAR'] \
            .replace(f'{fmt["DAY"]}1', day1) \
            .replace(f'{fmt["DAY"]}2', day2) \
            .replace(f'{fmt["MONTH"]}1', month1) \
            .replace(f'{fmt["MONTH"]}2', month2) \
            .replace(f'{fmt["YEAR"]}', year)

    @staticmethod
    def format_date_range_different_year(start_str: str, end_str: str, language_code: str) -> str:
        start_date = DateTimeService.string_to_date(start_str)
        end_date = DateTimeService.string_to_date(end_str)

        if start_date >= end_date:
            raise ValueError("End date must be greater than start date.")

        if start_date.year == end_date.year:
            raise ValueError("Start date and end date must be in different years.")

        fmt = settings.ALL_DATE_FORMATS[language_code]

        return date_format(start_date, fmt['DATE_FORMAT']) + \
            ' - ' + \
            date_format(end_date, fmt['DATE_FORMAT'])

    @staticmethod
    def format_date(date_str: str, language_code: str) -> str:
        date_obj = DateTimeService.string_to_date(date_str)
        fmt = settings.ALL_DATE_FORMATS[language_code]
        return date_format(date_obj, fmt['DATE_FORMAT'])

    @staticmethod
    def format_date_range(start_str: str, end_str: str, language_code: str) -> str:
        start_date = DateTimeService.string_to_date(start_str)
        end_date = DateTimeService.string_to_date(end_str)

        if start_date == end_date:
            return DateTimeService.format_date(start_str, language_code)

        if start_date.year == end_date.year:
            if start_date.month == end_date.month:
                return DateTimeService.format_date_range_same_month(start_str, end_str, language_code)
            else:
                return DateTimeService.format_date_range_same_year(start_str, end_str, language_code)
        else:
            return DateTimeService.format_date_range_different_year(start_str, end_str, language_code)

    @staticmethod
    def split_date_ranges(date_ranges_str: str, language_code: str) -> list:
        components = []

        for date_range in date_ranges_str.split(', '):
            if ' - ' in date_range:
                start, end = date_range.split(' - ')
                components.append(
                    {
                        'range': DateTimeService.format_date_range(start, end, language_code),
                        'start': start,
                        'end': end
                    }
                )
            else:
                components.append(
                    {
                        'date': DateTimeService.format_date(date_range, language_code),
                        'start': date_range,
                        'end': date_range
                    }
                )

        return components
