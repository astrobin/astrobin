import time
from datetime import datetime, date, timedelta


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
