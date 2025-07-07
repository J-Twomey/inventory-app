import datetime
import pytest
from typing import Any

import src.schemas as schemas


@pytest.mark.parametrize(
    ('value'),
    (
        pytest.param(None, id='none_value'),
        pytest.param('', id='empty_string'),
    ),
)
def test_parse_nullable_bool_no_parse(value: str | None) -> None:
    result = schemas.parse_nullable_bool(value)
    assert result is None


def test_parse_nullable_bool_invalid_format() -> None:
    value = 'null'
    with pytest.raises(ValueError, match='Invalid value passed to parse_nullable_bool: null'):
        schemas.parse_nullable_bool(value)


def test_parse_nullable_bool_false_case() -> None:
    value = 'false'
    result = schemas.parse_nullable_bool(value)
    assert not result


def test_parse_nullable_bool_true_case() -> None:
    value = 'true'
    result = schemas.parse_nullable_bool(value)
    assert result


@pytest.mark.parametrize(
    ('value'),
    (
        pytest.param(None, id='none_value'),
        pytest.param('', id='empty_string'),
    ),
)
def test_parse_nullable_date_no_parse(value: str | None) -> None:
    result = schemas.parse_nullable_date(value)
    assert result is None


def test_parse_nullable_date_invalid_date_format() -> None:
    input_str = '20250505'
    with pytest.raises(ValueError):
        schemas.parse_nullable_date(input_str)


def test_parse_nullable_date_do_parse() -> None:
    input_str = '2025-05-05'
    result = schemas.parse_nullable_date(input_str)
    assert result == datetime.date(2025, 5, 5)


def test_set_if_value_do_set() -> None:
    input_dict: dict[str, int] = {}
    key = 'a'
    value = 1
    schemas.set_if_value(input_dict, key, value)
    assert input_dict[key] == value


@pytest.mark.parametrize(
    ('value'),
    (
        pytest.param(None, id='none_value'),
        pytest.param('', id='empty_string'),
        pytest.param([], id='empty_list'),
        pytest.param({}, id='empty_dict'),
    ),
)
def test_set_if_value_no_set(value: Any) -> None:
    input_dict: dict[str, Any] = {}
    key = 'a'
    schemas.set_if_value(input_dict, key, value)
    assert len(input_dict) == 0


@pytest.mark.parametrize(
    ('sub_nums', 'fees', 'expected'),
    (
        pytest.param(['1', '2'], ['10', '20'], {1: 10, 2: 20}, id='simple_case'),
        pytest.param(['1', '2', ''], ['10', '20', ''], {1: 10, 2: 20}, id='remove_empty_string'),
    ),
)
def test_build_grading_fee_dict(
        sub_nums: list[str],
        fees: list[str],
        expected: dict[int, int],
) -> None:
    result = schemas.build_grading_fee_dict(sub_nums=sub_nums, fees=fees)
    assert result == expected


def test_build_grading_fee_dict_uneven_length() -> None:
    sub_nums = ['1', '2', '3']
    fees = ['10', '20']
    with pytest.raises(ValueError):
        schemas.build_grading_fee_dict(sub_nums=sub_nums, fees=fees)
