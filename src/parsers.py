from datetime import (
    date,
    datetime,
)
from typing import (
    Callable,
    Type,
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
    enum_cls: Type[E],
) -> E:
    try:
        return enum_cls[value.upper()]
    except KeyError:
        raise ValueError(f'Invalid {enum_cls.__name__}: {value}')


def parse_nullable_enum(
    value: str | None,
    enum_cls: Type[E],
) -> E | None:
    if value == '' or value is None:
        return None
    else:
        try:
            return enum_cls[value.upper()]
        except KeyError:
            raise ValueError(f'Invalid {enum_cls.__name__}: {value}')


def parse_to_qualifiers_list(values: list[str] | None) -> list[Qualifier]:
    if values is None:
        return []
    else:
        return [Qualifier[x.upper()] for x in values]


def parse_nullable(
    value: str | None,
    parser: Callable[[str], T],
) -> T | None:
    if value is None or value == '':
        return None
    else:
        return parser(value)


def parse_nullable_bool(value: str | None) -> bool | None:
    if value is None or value == '':
        return None
    elif value == 'true':
        return True
    elif value == 'false':
        return False
    else:
        raise ValueError(f'Invalid value passed to parse_nullable_bool: {value}')


def parse_nullable_date(date_str: str | None) -> date | None:
    if date_str is None or date_str == '':
        return None
    return datetime.strptime(date_str, '%Y-%m-%d').date()


def parse_nullable_percent(value: str | None) -> float | None:
    value_parsed = parse_nullable(value, float)
    if value_parsed is not None:
        value_parsed /= 100.
    return value_parsed


def parse_submission_update_field(
    field: str,
    value: str | None,
) -> date | int | GradingCompany | None:
    if value in ('', None):
        return None
    if 'date' in field:
        return parse_nullable_date(value)
    elif field == 'submission_number':
        return parse_nullable(value, int)
    elif field == 'submission_company':
        return parse_nullable_enum(value, GradingCompany)
    else:
        raise ValueError(f'Unsupported editable field: {field}')
