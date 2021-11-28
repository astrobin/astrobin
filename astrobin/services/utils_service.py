from datetime import datetime, timedelta

from common.services import DateTimeService


class UtilsService:
    @staticmethod
    def show_10_year_anniversary_logo() -> bool:
        today = DateTimeService.today()

        first_code_anniversary = datetime(2020, 11, 27).date()
        publication_anniversary = datetime(2021, 11, 27).date()

        return today in (first_code_anniversary, publication_anniversary)

    @staticmethod
    def unique(sequence):
        # Return unique items preserving order.
        seen = set()
        return [x for x in sequence if not (x in seen or seen.add(x))]
