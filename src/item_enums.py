import json
from enum import Enum
from typing import (
    Type,
    TypeVar,
)

from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.types import (
    TypeDecorator,
    TEXT,
)


class Category(Enum):
    CARD = 0
    PACK = 1
    BOX = 2


class Language(Enum):
    JAPANESE = 0
    ENGLISH = 1
    FRENCH = 2
    GERMAN = 3
    SPANISH = 4
    ITALIAN = 5
    DUTCH = 6
    PORTUGUESE = 7
    POLISH = 8
    RUSSIAN = 9
    LATIN_AMERICAN = 10
    CHINESE_SIMPLIFIED = 11
    CHINESE_TRADITIONAL = 12
    KOREAN = 13
    THAI = 14
    INDONESIAN = 15


class ObjectVariant(Enum):
    STANDARD = 0
    GROUP_PURCHASE = 1
    GROUP_SALE = 2


class Status(Enum):
    CLOSED = 0
    STORAGE = 1
    LISTED = 2
    VAULT = 3
    SUBMITTED = 4
    ORDER = 5


class Intent(Enum):
    KEEP = 0
    SELL = 1
    GRADE = 2
    TBD = 3


class Qualifier(Enum):
    UNLIMITED = 0
    FIRST_EDITION = 1
    NON_HOLO = 2
    REVERSE_HOLO = 3
    CRYSTAL = 4


class GradingCompany(Enum):
    RAW = 0
    PSA = 1
    CGC = 2
    BGS = 3


class ListingType(Enum):
    NO_LIST = 0
    FIXED = 1
    AUCTION = 2


E = TypeVar('E', bound=Enum)


class EnumList(TypeDecorator[list[E]]):
    impl = TEXT
    cache_ok = True

    def __init__(
            self,
            enum_class: Type[E],
    ) -> None:
        self.enum_class = enum_class
        super().__init__()

    def process_bind_param(
            self,
            value: list[E] | list[int] | None,
            dialect: Dialect,
    ) -> str | None:
        if value is None:
            return None
        int_representations = []
        for v in value:
            if isinstance(v, self.enum_class):
                int_representations.append(v.value)
            elif isinstance(v, int):
                int_representations.append(v)
            else:
                raise ValueError(f'Expected {self.enum_class.__name__} or int, got {type(v)}')
        return json.dumps(int_representations)

    def process_result_value(
            self,
            value: str | None,
            dialect: Dialect,
    ) -> list[E] | None:
        if value is None:
            return None
        raw: list[int] = json.loads(value)
        return [self.enum_class(v) for v in raw]


# class IntEnum(TypeDecorator[int]):
#     impl = Integer
#     cache_ok = True

#     def __init__(
#             self,
#             enum_class: Type[E],
#     ) -> None:
#         self.enum_class = enum_class
#         super().__init__()

#     def process_bind_param(
#             self,
#             value: E | None,
#             dialect: Dialect,
#     ) -> int | None:
#         if value is None:
#             return None
#         return cast(int, value.value)

#     def process_result_value(
#             self,
#             value: int | None,
#             dialect: Dialect,
#     ) -> E | None:
#         if value is None:
#             return None
#         return cast(E, self.enum_class(value))
