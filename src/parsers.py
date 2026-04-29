from collections.abc import Callable
from datetime import (
    date,
    datetime,
)

from .helper_types import (
    E,
    T,
)
from .item_enums import (
    GradingCompany,
    Qualifier,
)


def parse_enum(
    value: str,
    enum_cls: type[E],
) -> E:
    try:
        return enum_cls[value.upper()]
    except KeyError:
        raise ValueError(f'Invalid {enum_cls.__name__}: {value}') from None


def parse_nullable_enum(
    value: str | None,
    enum_cls: type[E],
) -> E | None:
    if value == '' or value is None:
        return None
    try:
        return enum_cls[value.upper()]
    except KeyError:
        raise ValueError(f'Invalid {enum_cls.__name__}: {value}') from None


def parse_to_qualifiers_list(values: list[str] | None) -> list[Qualifier]:
    if values is None:
        return []
    return [Qualifier[x.upper()] for x in values]


def parse_nullable(
    value: str | None,
    parser: Callable[[str], T],
) -> T | None:
    if value is None or value == '':
        return None
    return parser(value)


def parse_nullable_bool(value: str | None) -> bool | None:
    if value is None or value == '':
        return None
    if value == 'true':
        return True
    if value == 'false':
        return False
    raise ValueError(f'Invalid value passed to parse_nullable_bool: {value}')


def parse_nullable_date(date_str: str | None) -> date | None:
    if date_str is None or date_str == '':
        return None
    return datetime.strptime(date_str, '%Y-%m-%d').date()


def parse_nullable_percent(value: str | None) -> float | None:
    value_parsed = parse_nullable(value, float)
    if value_parsed is not None:
        value_parsed /= 100.0
    return value_parsed


def parse_submission_update_field(
    field: str,
    value: str | None,
) -> date | int | GradingCompany | None:
    if value in ('', None):
        return None
    if 'date' in field:
        return parse_nullable_date(value)
    if field == 'submission_number':
        return parse_nullable(value, int)
    if field == 'submission_company':
        return parse_nullable_enum(value, GradingCompany)
    raise ValueError(f'Unsupported editable field: {field}')
