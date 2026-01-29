import json
from enum import Enum
from typing import Type

from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.types import (
    Integer,
    TypeDecorator,
    TEXT,
)

from .helper_types import EInt


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
        mapping = {
            Status.CLOSED: [],
            Status.STORAGE: listing_fields + sale_fields,
            Status.LISTED: sale_fields,
            Status.VAULT: listing_fields + sale_fields,
            Status.SUBMITTED: listing_fields + sale_fields,
            Status.ORDER: listing_fields + sale_fields,
        }
        return mapping[self]


class Intent(Enum):
    KEEP = 0
    SELL = 1
    GRADE = 2
    CRACK = 3
    TBD = 4

    @property
    def allowed_statuses(self) -> list[Status]:
        all_ok = [Status.STORAGE, Status.VAULT, Status.ORDER]
        mapping = {
            Intent.KEEP: all_ok,
            Intent.SELL: all_ok + [Status.CLOSED, Status.LISTED],
            Intent.GRADE: all_ok + [Status.SUBMITTED],
            Intent.CRACK: all_ok,
            Intent.TBD: all_ok,
        }
        return mapping[self]


class Qualifier(Enum):
    UNLIMITED = 0
    FIRST_EDITION = 1
    NON_HOLO = 2
    REVERSE_HOLO = 3
    SPECIAL_REVERSE_HOLO = 4
    CRYSTAL = 5
    PRIME = 6
    BREAK = 7
    SUPER_RARE = 8
    HYPER_RARE = 9
    CHARACTER_RARE = 10
    ART_RARE = 11
    SPECIAL_ART_RARE = 12


class GradingCompany(Enum):
    RAW = 0
    PSA = 1
    CGC = 2
    BGS = 3


class ListingType(Enum):
    NO_LIST = 0
    FIXED = 1
    AUCTION = 2


class EnumList(TypeDecorator[list[EInt]]):
    impl = TEXT
    cache_ok = True

    def __init__(
            self,
            enum_class: Type[EInt],
    ) -> None:
        self.enum_class = enum_class
        super().__init__()

    def process_bind_param(
            self,
            value: list[EInt] | list[int] | None,
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
    ) -> list[EInt] | None:
        if value is None:
            return None
        raw: list[int] = json.loads(value)
        return [self.enum_class(v) for v in raw]


class EnumInt(TypeDecorator[EInt]):
    impl = Integer
    cache_ok = True

    def __init__(
            self,
            enum_cls: Type[EInt],
    ) -> None:
        self.enum_cls = enum_cls
        super().__init__()

    def process_bind_param(
            self,
            value: EInt | None,
            dialect: Dialect,
    ) -> int | None:
        if value is None:
            return None
        # elif isinstance(value, Enum):
        return value.value
        # return value

    def process_result_value(
            self,
            value: int | None,
            dialect: Dialect,
    ) -> EInt | None:
        if value is None:
            return None
        return self.enum_cls(value)
