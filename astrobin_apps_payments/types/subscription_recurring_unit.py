from enum import Enum


class SubscriptionRecurringUnit(Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"

    def __str__(self):
        return self.value

    @classmethod
    def choices(cls):
        return tuple((i.name, i.value) for i in cls)

    @classmethod
    def from_string(cls, value_str):
        if value_str is None:
            return None

        for member in cls:
            if member.name.lower() == value_str.lower():
                return member
        raise ValueError(f"Invalid enum value: {value_str}")
