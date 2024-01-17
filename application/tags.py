from enum import Enum


class TodoTags(Enum):
    education = "Education"
    personal = "Personal"
    plan = "Plan"

    @classmethod
    def contains(cls, value):
        return any(value == item.value for item in cls)


class Users(Enum):
    user1 = "2021-3-26-cha"
    user2 = "2021-3-04-zva"
    user3 = "2021-3-12-pro"


class Source(Enum):
    source_created = "Created"
    source_generated = "Generated"
    source_exported = "Exported"