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
    def human_time_duration(seconds):
        if seconds is None or seconds == 0:
            return '0'

        hours, reminder = divmod(seconds, 60 * 60)
        minutes, reminder = divmod(reminder, 60)
        seconds, reminder = divmod(reminder, 1)

        parts = []

        if hours > 0:
            parts.append('{}{}'.format(hours, 'h'))

        if minutes > 0:
            parts.append('{}{}'.format(minutes, '&prime;'))

        if seconds > 0:
            parts.append('{}{}'.format(seconds, '&Prime;'))

        if reminder > 0:
            parts.append('{}'.format(reminder).replace('0.', '.'))

        return ' '.join(parts)
