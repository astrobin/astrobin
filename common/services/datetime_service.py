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
