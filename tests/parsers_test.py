from datetime import date

import pytest

from src import (
    helper_types,
    item_enums,
    parsers,
)


def test_parse_enum() -> None:
    input_str = 'pack'
    result = parsers.parse_enum(input_str, item_enums.Category)
    assert result == item_enums.Category.PACK


def test_parse_enum_invalid_input() -> None:
    input_str = 'null'
    with pytest.raises(ValueError, match='Invalid Category: null'):
        parsers.parse_enum(input_str, item_enums.Category)


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


def test_parse_to_qualifiers_list_empty_input() -> None:
    input_list: list[str] = []
    result = parsers.parse_to_qualifiers_list(input_list)
    assert result == []


def test_parse_to_qualifiers_list_do_parse() -> None:
    input_list = ['CRYSTAL', 'UNLIMITED']
    result = parsers.parse_to_qualifiers_list(input_list)
    assert result == [item_enums.Qualifier.CRYSTAL, item_enums.Qualifier.UNLIMITED]


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
def test_parse_nullable_bool_no_parse(value: str | None) -> None:
    result = parsers.parse_nullable_bool(value)
    assert result is None


def test_parse_nullable_bool_invalid_format() -> None:
    value = 'null'
    with pytest.raises(ValueError, match='Invalid value passed to parse_nullable_bool: null'):
        parsers.parse_nullable_bool(value)


def test_parse_nullable_bool_false_case() -> None:
    value = 'false'
    result = parsers.parse_nullable_bool(value)
    assert not result


def test_parse_nullable_bool_true_case() -> None:
    value = 'true'
    result = parsers.parse_nullable_bool(value)
    assert result


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


@pytest.mark.parametrize(
    ('value', 'expected'),
    [
        pytest.param(None, None, id='none_value'),
        pytest.param('100', 1.0, id='positive_percent'),
        pytest.param('0', 0.0, id='zero_percent'),
        pytest.param('-50', -0.5, id='negative_percent'),
    ],
)
def test_parse_nullable_percent(
    value: str | None,
    expected: float | None,
) -> None:
    result = parsers.parse_nullable_percent(value)
    assert result == expected
