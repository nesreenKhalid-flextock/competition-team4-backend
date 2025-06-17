from enum import Enum


class GroupOrderStatusEnum(Enum):
    OPEN = "open"
    LOCKED = "locked"
    ORDERED = "ordered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    @classmethod
    def choices(cls):
        return [(tag.name, tag.value) for tag in cls]
