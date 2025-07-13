import datetime
import pytest
from typing import Any

from pydantic import ValidationError

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


def test_item_base_submission_numbers(item_base_factory: ItemBaseFactory) -> None:
    grading_fees = {1: 10, 2: 20}
    item = item_base_factory.get(grading_fee=grading_fees)
    assert item.submission_numbers == [1, 2]


def test_item_base_submission_numbers_empty(item_base_factory: ItemBaseFactory) -> None:
    grading_fees: dict[int, int] = {}
    item = item_base_factory.get(grading_fee=grading_fees)
    assert item.submission_numbers == []


def test_item_base_total_cost(item_base_factory: ItemBaseFactory) -> None:
    purchase_price = 555
    grading_fees = {1: 10, 2: 20}
    item = item_base_factory.get(purchase_price=purchase_price, grading_fee=grading_fees)
    assert item.total_cost == 585


@pytest.mark.parametrize(
    ('shipping', 'sale_fee', 'expected_total'),
    (
        pytest.param(None, None, None, id='no_fees'),
        pytest.param(None, 8.7, None, id='no_shipping'),
        pytest.param(5.5, None, None, id='no_sale_fee'),
        pytest.param(5.5, 8.7, 14.2, id='with_fees'),
    ),
)
def test_item_base_total_fees(
        item_base_factory: ItemBaseFactory,
        shipping: float | None,
        sale_fee: float | None,
        expected_total: float | None,
) -> None:
    item = item_base_factory.get(shipping=shipping, sale_fee=sale_fee)
    assert item.total_fees == expected_total


@pytest.mark.parametrize(
    ('sale_total', 'shipping', 'sale_fee', 'expected_return'),
    (
        pytest.param(None, None, None, None, id='no_fees'),
        pytest.param(None, 5.34, 8.66, None, id='no_sale_total'),
        pytest.param(11.23, None, 8.66, None, id='no_total_fee'),
        pytest.param(15.31, 5.54, 8.66, 1.11, id='net_positive'),
        pytest.param(10.35, 5.54, 8.66, -3.85, id='net_negative'),
    ),
)
def test_item_base_return_usd(
        item_base_factory: ItemBaseFactory,
        sale_total: float | None,
        shipping: float | None,
        sale_fee: float | None,
        expected_return: float | None,
) -> None:
    item = item_base_factory.get(sale_total=sale_total, shipping=shipping, sale_fee=sale_fee)
    assert item.return_usd == expected_return


@pytest.mark.parametrize(
    ('sale_total', 'shipping', 'sale_fee', 'usd_to_jpy_rate', 'expected_return'),
    (
        pytest.param(None, None, None, None, None, id='no_fees'),
        pytest.param(9.64, 3.21, None, 140.55, None, id='no_return_usd'),
        pytest.param(9.64, 3.21, 2.87, None, None, id='no_exchange_rate'),
        pytest.param(9.64, 3.21, 2.87, 140.55, 500, id='net_positive'),
        pytest.param(5.49, 3.27, 2.99, 140.55, -108, id='net_negative'),
    ),
)
def test_item_base_return_jpy(
        item_base_factory: ItemBaseFactory,
        sale_total: float | None,
        shipping: float | None,
        sale_fee: float | None,
        usd_to_jpy_rate: float | None,
        expected_return: int | None,
) -> None:
    item = item_base_factory.get(
        sale_total=sale_total,
        shipping=shipping,
        sale_fee=sale_fee,
        usd_to_jpy_rate=usd_to_jpy_rate,
    )
    assert item.return_jpy == expected_return


@pytest.mark.parametrize(
    (
        'purchase_price',
        'grading_fees',
        'sale_total',
        'shipping',
        'sale_fee',
        'usd_to_jpy_rate',
        'expected_net',
    ),
    (
        pytest.param(10, {1: 100}, None, None, None, None, None, id='no_sale'),
        pytest.param(10, {1: 100}, 9.64, 3.21, 2.87, 140.55, 390, id='net_positive'),
        pytest.param(1000, {1: 100}, 9.64, 3.21, 2.87, 140.55, -600, id='positive_ret_net_neg'),
        pytest.param(10, {1: 100}, 5.49, 3.27, 2.99, 140.55, -218, id='negative_ret_net_neg'),
    ),
)
def test_item_base_net_jpy(
        item_base_factory: ItemBaseFactory,
        purchase_price: int,
        grading_fees: dict[int, int],
        sale_total: float | None,
        shipping: float | None,
        sale_fee: float | None,
        usd_to_jpy_rate: float | None,
        expected_net: int | None,
) -> None:
    item = item_base_factory.get(
        purchase_price=purchase_price,
        grading_fee=grading_fees,
        sale_total=sale_total,
        shipping=shipping,
        sale_fee=sale_fee,
        usd_to_jpy_rate=usd_to_jpy_rate,
    )
    assert item.net_jpy == expected_net


@pytest.mark.parametrize(
    (
        'purchase_price',
        'grading_fees',
        'sale_total',
        'shipping',
        'sale_fee',
        'usd_to_jpy_rate',
        'expected_percent',
    ),
    (
        pytest.param(10, {1: 100}, None, None, None, None, None, id='no_sale'),
        pytest.param(0, {}, 9.55, 3.33, 2.11, 140.55, 0., id='no_costs'),
        pytest.param(10, {1: 100}, 9.64, 3.21, 2.87, 140.55, 354.55, id='net_positive'),
        pytest.param(1000, {1: 100}, 9.64, 3.21, 2.87, 140.55, -54.55, id='positive_ret_net_neg'),
        pytest.param(10, {1: 100}, 5.49, 3.27, 2.99, 140.55, -198.18, id='negative_ret_net_neg'),
    ),
)
def test_item_base_net_percent(
        item_base_factory: ItemBaseFactory,
        purchase_price: int,
        grading_fees: dict[int, int],
        sale_total: float | None,
        shipping: float | None,
        sale_fee: float | None,
        usd_to_jpy_rate: float | None,
        expected_percent: float | None,
) -> None:
    item = item_base_factory.get(
        purchase_price=purchase_price,
        grading_fee=grading_fees,
        sale_total=sale_total,
        shipping=shipping,
        sale_fee=sale_fee,
        usd_to_jpy_rate=usd_to_jpy_rate,
    )
    assert item.net_percent == expected_percent


@pytest.mark.parametrize(
    ('field', 'input_value', 'expected_value'),
    (
        pytest.param('name', 'kari', 'kari', id='string_field_not_empty'),
        pytest.param('purchase_price', 5, 5, id='int_field_not_empty'),
        pytest.param('grade', 5., 5., id='float_field_not_empty'),
        pytest.param('grade', None, None, id='none_field_not_empty'),
        pytest.param(
            'category',
            item_enums.Category.BOX,
            item_enums.Category.BOX,
            id='enum_field_not_empty',
        ),
        pytest.param(
            'purchase_date',
            datetime.date(1999, 12, 31),
            datetime.date(1999, 12, 31),
            id='date_field_not_empty',
        ),
        pytest.param('cracked_from', [1, 2], [1, 2], id='excluded_field'),
    ),
)
def test_item_base_empty_str_to_none_validator(
        item_base_factory: ItemBaseFactory,
        field: str,
        input_value: Any,
        expected_value: Any,
) -> None:
    field_settings = {field: input_value}
    item = item_base_factory.get(**field_settings)
    actual_value = getattr(item, field)
    assert actual_value == expected_value


def test_item_base_required_field_not_allowed_as_empty_string(
        item_base_factory: ItemBaseFactory,
) -> None:
    with pytest.raises(ValidationError):
        item_base_factory.get(name='')


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
