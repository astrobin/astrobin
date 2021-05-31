from datetime import datetime, timedelta

from common.services import DateTimeService


class UtilsService:
    @staticmethod
    def show_10_year_anniversary_logo():
        # type: () -> bool

        today = DateTimeService.today()

        first_code_anniversary = datetime(2020, 11, 27).date()
        publication_anniversary = datetime(2021, 11, 27).date()
        one_week = timedelta(days=7)

        return \
            first_code_anniversary <= today < first_code_anniversary + one_week or \
            publication_anniversary <= today < publication_anniversary + one_week

    @staticmethod
    def unique(sequence):
        # Return unique items preserving order.
        seen = set()
        return [x for x in sequence if not (x in seen or seen.add(x))]
