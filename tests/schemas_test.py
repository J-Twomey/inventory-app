import pytest
from datetime import date
from typing import Any

from pydantic import ValidationError

import src.item_enums as item_enums
import src.schemas as schemas
from .conftest import (
    ItemBaseFactory,
    ItemCreateFactory,
)


@pytest.mark.parametrize(
    ('field', 'input_value', 'expected_value'),
    (
        pytest.param('name', 'kari', 'kari', id='string_field_not_empty'),
        pytest.param('purchase_price', 5, 5, id='int_field_not_empty'),
        pytest.param('list_price', 5., 5., id='float_field_not_empty'),
        pytest.param(
            'category',
            item_enums.Category.BOX,
            item_enums.Category.BOX,
            id='enum_field_not_empty',
        ),
        pytest.param(
            'purchase_date',
            date(1999, 12, 31),
            date(1999, 12, 31),
            id='date_field_not_empty',
        ),
        pytest.param('group_discount', False, False, id='excluded_field'),
    ),
)
def test_item_base_empty_str_to_none_validator(
    item_base_factory: ItemBaseFactory,
    field: str,
    input_value: Any,
    expected_value: Any,
) -> None:
    field_settings = {
        field: input_value,
        'status': item_enums.Status.LISTED,
        'intent': item_enums.Intent.SELL,
        'list_date': date(2025, 5, 5),
        'list_type': item_enums.ListingType.FIXED,
    }
    if 'list_price' not in field_settings:
        field_settings['list_price'] = 1.
    item = item_base_factory.get(**field_settings)
    actual_value = getattr(item, field)
    assert actual_value == expected_value


@pytest.mark.parametrize(
    ('input_value', 'expected_value'),
    (
        pytest.param('', [], id='empty_string'),
        pytest.param([], [], id='empty_list'),
        pytest.param(
            'UNLIMITED,CRYSTAL',
            [item_enums.Qualifier.UNLIMITED, item_enums.Qualifier.CRYSTAL],
            id='str_input',
        ),
        pytest.param(
            [item_enums.Qualifier.UNLIMITED, item_enums.Qualifier.CRYSTAL],
            [item_enums.Qualifier.UNLIMITED, item_enums.Qualifier.CRYSTAL],
            id='list_input',
        ),
    ),
)
def test_item_base_parse_qualifiers_validator(
    item_base_factory: ItemBaseFactory,
    input_value: str | list[item_enums.Qualifier],
    expected_value: list[item_enums.Qualifier],
) -> None:
    item = item_base_factory.get(qualifiers=input_value)  # type: ignore[arg-type]
    actual_value = item.qualifiers
    assert actual_value == expected_value


def test_item_base_parse_qualifiers_wrong_type_input(item_base_factory: ItemBaseFactory) -> None:
    with pytest.raises(ValidationError) as e:
        item_base_factory.get(qualifiers=5)  # type: ignore[arg-type]
    error_msg = e.value.errors()[0]['msg']
    assert 'Qualifiers must be provided as str or list[Qualifier]' in error_msg


def test_item_base_list_date_not_before_purchase_date(item_base_factory: ItemBaseFactory) -> None:
    item_base_factory.get(
        purchase_date=date(2025, 5, 5),
        status=item_enums.Status.LISTED,
        list_date=date(2025, 5, 6),
        list_price=1.,
        list_type=item_enums.ListingType.FIXED,
    )


def test_item_base_list_date_before_purchase_date(item_base_factory: ItemBaseFactory) -> None:
    with pytest.raises(ValidationError) as e:
        item_base_factory.get(
            purchase_date=date(2025, 5, 5),
            status=item_enums.Status.LISTED,
            list_date=date(2025, 5, 4),
            list_price=1.,
            list_type=item_enums.ListingType.FIXED,
        )
    error_msg = e.value.errors()[0]['msg']
    assert (
        'Listing date cannot be before purchase date (got listing date: 2025-05-04, '
        'purchase date: 2025-05-05)'
    ) in error_msg


def test_item_base_sale_date_not_before_list_date(item_base_factory: ItemBaseFactory) -> None:
    item_base_factory.get(
        purchase_date=date(2025, 5, 5),
        status=item_enums.Status.CLOSED,
        list_date=date(2025, 5, 6),
        list_price=1.,
        list_type=item_enums.ListingType.FIXED,
        sale_date=date(2025, 5, 6),
        sale_total=1.,
        shipping=0.,
        sale_fee=0.,
        usd_to_jpy_rate=100,
    )


def test_item_base_sale_date_before_list_date(item_base_factory: ItemBaseFactory) -> None:
    with pytest.raises(ValidationError) as e:
        item_base_factory.get(
            purchase_date=date(2025, 5, 5),
            status=item_enums.Status.CLOSED,
            list_date=date(2025, 5, 6),
            list_price=1.,
            list_type=item_enums.ListingType.FIXED,
            sale_date=date(2025, 5, 5),
            sale_total=1.,
            shipping=0.,
            sale_fee=0.,
            usd_to_jpy_rate=100,
        )
    error_msg = e.value.errors()[0]['msg']
    assert (
        'Sale date cannot be before listing date (got sale date: 2025-05-05, '
        'listing date: 2025-05-06)'
    ) in error_msg


def test_check_required_fields_based_on_status_no_error(
    item_base_factory: ItemBaseFactory,
) -> None:
    item_base_factory.get(
        purchase_date=date(2025, 5, 5),
        status=item_enums.Status.CLOSED,
        list_date=date(2025, 5, 6),
        list_price=1.,
        list_type=item_enums.ListingType.FIXED,
        sale_date=date(2025, 5, 6),
        sale_total=1.,
        shipping=0.,
        sale_fee=0.,
        usd_to_jpy_rate=100,
    )


def test_check_required_fields_based_on_status_error_case(
    item_base_factory: ItemBaseFactory,
) -> None:
    with pytest.raises(ValidationError) as e:
        item_base_factory.get(
            purchase_date=date(2025, 5, 5),
            status=item_enums.Status.CLOSED,
            list_date=date(2025, 5, 6),
            list_price=1.,
            list_type=item_enums.ListingType.FIXED,
            sale_date=date(2025, 5, 6),
            sale_total=None,
            shipping=0.,
            sale_fee=0.,
            usd_to_jpy_rate=100,
        )
    error_msg = e.value.errors()[0]['msg']
    assert "Status CLOSED requires the following missing fields: ['sale_total']" in error_msg


def test_check_required_null_fields_based_on_status_no_error(
    item_base_factory: ItemBaseFactory,
) -> None:
    item_base_factory.get(
        purchase_date=date(2025, 5, 5),
        status=item_enums.Status.SUBMITTED,
    )


def test_check_required_null_fields_based_on_status_error_case(
    item_base_factory: ItemBaseFactory,
) -> None:
    with pytest.raises(ValidationError) as e:
        item_base_factory.get(
            purchase_date=date(2025, 5, 5),
            status=item_enums.Status.SUBMITTED,
            list_date=date(2025, 5, 6),
        )
    error_msg = e.value.errors()[0]['msg']
    assert "Status SUBMITTED requires the following fields to be null: ['list_date']" in error_msg


def test_appropriate_listing_type_no_error_no_listing(item_base_factory: ItemBaseFactory) -> None:
    item_base_factory.get(
        purchase_date=date(2025, 5, 5),
        status=item_enums.Status.STORAGE,
        list_type=item_enums.ListingType.NO_LIST,
    )


def test_appropriate_listing_type_no_error_is_listed(item_base_factory: ItemBaseFactory) -> None:
    item_base_factory.get(
        purchase_date=date(2025, 5, 5),
        status=item_enums.Status.LISTED,
        list_type=item_enums.ListingType.FIXED,
        list_date=date(2025, 5, 6),
        list_price=1.,
    )


def test_appropriate_listing_type_no_error_is_closed(item_base_factory: ItemBaseFactory) -> None:
    item_base_factory.get(
        purchase_date=date(2025, 5, 5),
        status=item_enums.Status.CLOSED,
        list_type=item_enums.ListingType.AUCTION,
        list_date=date(2025, 5, 6),
        list_price=1.,
        sale_date=date(2025, 5, 6),
        sale_total=1.,
        sale_fee=0.1,
        shipping=0.1,
        usd_to_jpy_rate=150.,
    )


def test_appropriate_listing_type_listing_error(item_base_factory: ItemBaseFactory) -> None:
    with pytest.raises(ValidationError) as e:
        item_base_factory.get(
            purchase_date=date(2025, 5, 5),
            status=item_enums.Status.LISTED,
            list_type=item_enums.ListingType.NO_LIST,
            list_date=date(2025, 5, 6),
            list_price=1.,
        )
    error_msg = e.value.errors()[0]['msg']
    assert 'Item cannot have list_type of NO_LIST if listed or sold' in error_msg


def test_appropriate_listing_type_storage_error(item_base_factory: ItemBaseFactory) -> None:
    with pytest.raises(ValidationError) as e:
        item_base_factory.get(
            purchase_date=date(2025, 5, 5),
            status=item_enums.Status.STORAGE,
            list_type=item_enums.ListingType.FIXED,
        )
    error_msg = e.value.errors()[0]['msg']
    assert 'Item cannot have a list_type other than NO_LIST if not listed or sold' in error_msg


def test_appropriate_group_discount_no_discount(item_base_factory: ItemBaseFactory) -> None:
    item_base_factory.get(group_discount=False)


def test_appropriate_group_discount_no_error(item_base_factory: ItemBaseFactory) -> None:
    item_base_factory.get(
        purchase_date=date(2025, 5, 5),
        status=item_enums.Status.CLOSED,
        intent=item_enums.Intent.SELL,
        list_type=item_enums.ListingType.AUCTION,
        list_date=date(2025, 5, 6),
        list_price=1.,
        sale_date=date(2025, 5, 6),
        sale_total=1.,
        sale_fee=0.1,
        shipping=0.1,
        usd_to_jpy_rate=150.,
        group_discount=True,
    )


def test_appropriate_group_discount_error(item_base_factory: ItemBaseFactory) -> None:
    with pytest.raises(ValidationError) as e:
        item_base_factory.get(
            status=item_enums.Status.STORAGE,
            group_discount=True,
        )
    error_msg = e.value.errors()[0]['msg']
    assert 'Group discount cannot be assigned to an unsold item' in error_msg


def test_appropriate_audit_target_no_error(item_base_factory: ItemBaseFactory) -> None:
    item_base_factory.get(
        status=item_enums.Status.VAULT,
        audit_target=True,
    )


def test_appropriate_audit_target_listing_error(item_base_factory: ItemBaseFactory) -> None:
    with pytest.raises(ValidationError) as e:
        item_base_factory.get(
            purchase_date=date(2025, 5, 5),
            status=item_enums.Status.LISTED,
            intent=item_enums.Intent.SELL,
            list_type=item_enums.ListingType.AUCTION,
            list_date=date(2025, 5, 6),
            list_price=1.,
            audit_target=True,
        )
    error_msg = e.value.errors()[0]['msg']
    assert 'Item assigned as an audit target can not be listed or closed' in error_msg


def test_appropriate_audit_target_closed_error(item_base_factory: ItemBaseFactory) -> None:
    with pytest.raises(ValidationError) as e:
        item_base_factory.get(
            purchase_date=date(2025, 5, 5),
            status=item_enums.Status.CLOSED,
            intent=item_enums.Intent.SELL,
            list_type=item_enums.ListingType.AUCTION,
            list_date=date(2025, 5, 6),
            list_price=1.,
            sale_date=date(2025, 5, 6),
            sale_total=1.,
            sale_fee=0.1,
            shipping=0.1,
            usd_to_jpy_rate=150.,
            audit_target=True,
        )
    error_msg = e.value.errors()[0]['msg']
    assert 'Item assigned as an audit target can not be listed or closed' in error_msg


def test_appropriate_status_based_on_intent_no_error(
    item_create_factory: ItemCreateFactory,
) -> None:
    item_create_factory.get(
        status=item_enums.Status.SUBMITTED,
        intent=item_enums.Intent.GRADE,
    )


def test_appropriate_status_based_on_intent_error_case(
    item_create_factory: ItemCreateFactory,
) -> None:
    with pytest.raises(ValidationError) as e:
        item_create_factory.get(
            status=item_enums.Status.SUBMITTED,
            intent=item_enums.Intent.SELL,
        )
    error_msg = e.value.errors()[0]['msg']
    assert 'Item can not have status of SUBMITTED with intent of SELL' in error_msg


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
    result = schemas.parse_nullable_enum(input_str, item_enums.Category)
    assert result == item_enums.Category.PACK


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
    assert result == date(2025, 5, 5)


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
    ('value', 'expected'),
    (
        pytest.param(None, None, id='none_value'),
        pytest.param('100', 1., id='positive_percent'),
        pytest.param('0', 0., id='zero_percent'),
        pytest.param('-50', -0.5, id='negative_percent'),
    ),
)
def test_parse_nullable_percent(
    value: str | None,
    expected: float | None,
) -> None:
    result = schemas.parse_nullable_percent(value)
    assert result == expected
