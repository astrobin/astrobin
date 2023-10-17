import re
from datetime import datetime
from typing import List

from common.services import DateTimeService


class UtilsService:
    @staticmethod
    def unique(sequence):
        # Return unique items preserving order.
        seen = set()
        return [x for x in sequence if not (x in seen or seen.add(x))]

    @staticmethod
    def split_text_alphanumerically(s: str) -> List[str]:
        return re.findall(r"[^\W\d_]+|\d+", s)

    @staticmethod
    def anonymize_email(email):
        username, domain = email.split('@')

        if len(username) <= 2:
            username = '*' * len(username)
        else:
            username = f"{username[0]}****{username[-1]}"

        return f"{username}@{domain}"
