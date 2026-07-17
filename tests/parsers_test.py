from datetime import date

import pytest

from src import (
    helper_types,
    item_enums,
    parsers,
)


def test_parse_nullable_enum_do_parse_to_enum() -> None:
    input_str = 'pack'
    result = parsers.parse_nullable_enum(input_str, item_enums.Category)
    assert result == item_enums.Category.PACK


@pytest.mark.parametrize(
    ('value'),
    [
        pytest.param(None, id='none_value'),
        pytest.param('', id='empty_string'),
    ],
)
def test_parse_nullable_enum_no_parse(value: str | None) -> None:
    result = parsers.parse_nullable_enum(value, item_enums.Category)
    assert result is None


def test_parse_nullable_enum_invalid_input() -> None:
    input_str = 'null'
    with pytest.raises(ValueError, match='Invalid Category: null'):
        parsers.parse_nullable_enum(input_str, item_enums.Category)


@pytest.mark.parametrize(
    ('value'),
    [
        pytest.param(None, id='none_value'),
        pytest.param('', id='empty_string'),
    ],
)
def test_parse_nullable_no_parse(value: str | None) -> None:
    result = parsers.parse_nullable(value, str)
    assert result is None


@pytest.mark.parametrize(
    ('value', 'parser'),
    [
        pytest.param('a', str, id='parse_string'),
        pytest.param('1', int, id='parse_int'),
        pytest.param('1.', float, id='parse_float'),
    ],
)
def test_parse_nullable_do_parse(
    value: str,
    parser: type[helper_types.T],
) -> None:
    result = parsers.parse_nullable(value, parser)
    assert isinstance(result, parser)


@pytest.mark.parametrize(
    ('value'),
    [
        pytest.param(None, id='none_value'),
        pytest.param('', id='empty_string'),
    ],
)
def test_parse_nullable_date_no_parse(value: str | None) -> None:
    result = parsers.parse_nullable_date(value)
    assert result is None


def test_parse_nullable_date_invalid_date_format() -> None:
    input_str = '20250505'
    with pytest.raises(
        ValueError,
        match=f"time data '{input_str}' does not match format '%Y-%m-%d'",
    ):
        parsers.parse_nullable_date(input_str)


def test_parse_nullable_date_do_parse() -> None:
    input_str = '2025-05-05'
    result = parsers.parse_nullable_date(input_str)
    assert result == date(2025, 5, 5)
