import datetime
import pytest
from typing import Any

import src.item_enums as item_enums
import src.schemas as schemas
from .conftest import ItemBaseFactory


@pytest.mark.parametrize(
    ('grading_fees', 'expected_total'),
    (
        pytest.param({}, 0, id='no_grading_fees'),
        pytest.param({1: 10}, 10, id='single_fee'),
        pytest.param({1: 10, 2: 20}, 30, id='multiple_fees'),
    ),
)
def test_item_base_grading_fee_total(
        item_base_factory: ItemBaseFactory,
        grading_fees: dict[int, int],
        expected_total: int,
) -> None:
    item = item_base_factory.get(grading_fee=grading_fees)
    assert item.grading_fee_total == expected_total


def test_parse_enum() -> None:
    input_str = 'pack'
    result = schemas.parse_enum(input_str, item_enums.Category)
    assert result == item_enums.Category.PACK


def test_parse_enum_invalid_input() -> None:
    input_str = 'null'
    with pytest.raises(ValueError, match='Invalid Category: null'):
        schemas.parse_enum(input_str, item_enums.Category)


def test_parse_nullable_enum_do_parse_to_enum() -> None:
    input_str = 'pack'
    result = schemas.parse_nullable_enum(input_str, item_enums.Category, as_int=False)
    assert result == item_enums.Category.PACK


def test_parse_nullable_enum_do_parse_to_int() -> None:
    input_str = 'pack'
    result = schemas.parse_nullable_enum(input_str, item_enums.Category, as_int=True)
    assert result == item_enums.Category.PACK.value


@pytest.mark.parametrize(
    ('value'),
    (
        pytest.param(None, id='none_value'),
        pytest.param('', id='empty_string'),
    ),
)
def test_parse_nullable_enum_no_parse(value: str | None) -> None:
    result = schemas.parse_nullable_enum(value, item_enums.Category)
    assert result is None


def test_parse_nullable_enum_invalid_input() -> None:
    input_str = 'null'
    with pytest.raises(ValueError, match='Invalid Category: null'):
        schemas.parse_nullable_enum(input_str, item_enums.Category)


def test_parse_to_qualifiers_list_empty_input() -> None:
    input_list: list[str] = []
    result = schemas.parse_to_qualifiers_list(input_list)
    assert result == []


def test_parse_to_qualifiers_list_do_parse() -> None:
    input_list = ['CRYSTAL', 'UNLIMITED']
    result = schemas.parse_to_qualifiers_list(input_list)
    assert result == [item_enums.Qualifier.CRYSTAL, item_enums.Qualifier.UNLIMITED]


@pytest.mark.parametrize(
    ('value'),
    (
        pytest.param(None, id='none_value'),
        pytest.param('', id='empty_string'),
    ),
)
def test_parse_nullable_no_parse(value: str | None) -> None:
    result = schemas.parse_nullable(value, str)
    assert result is None


@pytest.mark.parametrize(
    ('value', 'parser'),
    (
        pytest.param('a', str, id='parse_string'),
        pytest.param('1', int, id='parse_int'),
        pytest.param('1.', float, id='parse_float'),
    ),
)
def test_parse_nullable_do_parse(
        value: str,
        parser: type[schemas.T],
) -> None:
    result = schemas.parse_nullable(value, parser)
    assert isinstance(result, parser)


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


def test_parse_nullable_list_of_str_to_list_of_int() -> None:
    input_list = ['1', '2']
    result = schemas.parse_nullable_list_of_str_to_list_of_int(input_list)
    assert result == [1, 2]


def test_parse_nullable_list_of_str_to_list_of_int_none_case() -> None:
    input_list = None
    result = schemas.parse_nullable_list_of_str_to_list_of_int(input_list)
    assert result == []


def test_parse_nullable_list_of_str_to_list_of_int_with_empty_string() -> None:
    input_list = ['1', '', '2']
    result = schemas.parse_nullable_list_of_str_to_list_of_int(input_list)
    assert result == [1, 2]
