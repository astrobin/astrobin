import time
from datetime import datetime, date, timedelta


class DateTimeService:
    TIME_DURATION_UNITS = (
        ('h', 60 * 60),
        ('\'', 60),
        ('"', 1)
    )

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
    def human_time_duration(seconds):
        if seconds is None or seconds == 0:
            return '0'

        parts = []
        for unit, div in DateTimeService.TIME_DURATION_UNITS:
            amount, seconds = divmod(int(seconds), div)
            if amount > 0:
                parts.append('{}{}'.format(amount, unit))

        return ' '.join(parts)
