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

    @property
    def required_fields(self) -> list[str]:
        mapping = {
            Status.CLOSED: ['sale_total', 'sale_date', 'shipping', 'sale_fee', 'usd_to_jpy_rate'],
            Status.STORAGE: [],
            Status.LISTED: ['list_price', 'list_type', 'list_date'],
            Status.VAULT: [],
            Status.SUBMITTED: [],
            Status.ORDER: [],
        }
        return mapping[self]

    @property
    def required_to_be_null(self) -> list[str]:
        listing_fields = ['list_price', 'list_date']
        sale_fields = ['sale_total', 'sale_date', 'shipping', 'sale_fee', 'usd_to_jpy_rate']
        graded_fields = ['grade', 'cert']
        mapping = {
            Status.CLOSED: [],
            Status.STORAGE: listing_fields + sale_fields,
            Status.LISTED: sale_fields,
            Status.VAULT: listing_fields + sale_fields,
            Status.SUBMITTED: listing_fields + sale_fields + graded_fields,
            Status.ORDER: listing_fields + sale_fields,
        }
        return mapping[self]


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
