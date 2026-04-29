from datetime import date

import pytest
from pydantic import ValidationError

from src import (
    item_enums,
    schemas,
)

from .conftest import (
    ItemBaseFactory,
    ItemCreateFactory,
)


@pytest.mark.parametrize(
    ('field', 'input_value', 'expected_value'),
    [
        pytest.param('name', 'kari', 'kari', id='string_field_not_empty'),
        pytest.param('purchase_price', 5, 5, id='int_field_not_empty'),
        pytest.param('list_price', 5.0, 5.0, id='float_field_not_empty'),
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
    ],
)
def test_item_base_empty_str_to_none_validator(
    item_base_factory: ItemBaseFactory,
    field: str,
    input_value: str | float | date | item_enums.Category | bool,
    expected_value: str | float | date | item_enums.Category | bool,
) -> None:
    field_settings = {
        field: input_value,
        'status': item_enums.Status.LISTED,
        'intent': item_enums.Intent.SELL,
        'list_date': date(2025, 5, 5),
        'list_type': item_enums.ListingType.FIXED,
    }
    if 'list_price' not in field_settings:
        field_settings['list_price'] = 1.0
    item = item_base_factory.get(**field_settings)
    actual_value = getattr(item, field)
    assert actual_value == expected_value


@pytest.mark.parametrize(
    ('input_value', 'expected_value'),
    [
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
    ],
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
        list_price=1.0,
        list_type=item_enums.ListingType.FIXED,
    )


def test_item_base_list_date_before_purchase_date(item_base_factory: ItemBaseFactory) -> None:
    with pytest.raises(ValidationError) as e:
        item_base_factory.get(
            purchase_date=date(2025, 5, 5),
            status=item_enums.Status.LISTED,
            list_date=date(2025, 5, 4),
            list_price=1.0,
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
        list_price=1.0,
        list_type=item_enums.ListingType.FIXED,
        sale_date=date(2025, 5, 6),
        sale_total=1.0,
        shipping=0.0,
        sale_fee=0.0,
        usd_to_jpy_rate=100,
    )


def test_item_base_sale_date_before_list_date(item_base_factory: ItemBaseFactory) -> None:
    with pytest.raises(ValidationError) as e:
        item_base_factory.get(
            purchase_date=date(2025, 5, 5),
            status=item_enums.Status.CLOSED,
            list_date=date(2025, 5, 6),
            list_price=1.0,
            list_type=item_enums.ListingType.FIXED,
            sale_date=date(2025, 5, 5),
            sale_total=1.0,
            shipping=0.0,
            sale_fee=0.0,
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
        list_price=1.0,
        list_type=item_enums.ListingType.FIXED,
        sale_date=date(2025, 5, 6),
        sale_total=1.0,
        shipping=0.0,
        sale_fee=0.0,
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
            list_price=1.0,
            list_type=item_enums.ListingType.FIXED,
            sale_date=date(2025, 5, 6),
            sale_total=None,
            shipping=0.0,
            sale_fee=0.0,
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
        list_price=1.0,
    )


def test_appropriate_listing_type_no_error_is_closed(item_base_factory: ItemBaseFactory) -> None:
    item_base_factory.get(
        purchase_date=date(2025, 5, 5),
        status=item_enums.Status.CLOSED,
        list_type=item_enums.ListingType.AUCTION,
        list_date=date(2025, 5, 6),
        list_price=1.0,
        sale_date=date(2025, 5, 6),
        sale_total=1.0,
        sale_fee=0.1,
        shipping=0.1,
        usd_to_jpy_rate=150.0,
    )


def test_appropriate_listing_type_listing_error(item_base_factory: ItemBaseFactory) -> None:
    with pytest.raises(ValidationError) as e:
        item_base_factory.get(
            purchase_date=date(2025, 5, 5),
            status=item_enums.Status.LISTED,
            list_type=item_enums.ListingType.NO_LIST,
            list_date=date(2025, 5, 6),
            list_price=1.0,
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
        list_price=1.0,
        sale_date=date(2025, 5, 6),
        sale_total=1.0,
        sale_fee=0.1,
        shipping=0.1,
        usd_to_jpy_rate=150.0,
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
            list_price=1.0,
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
            list_price=1.0,
            sale_date=date(2025, 5, 6),
            sale_total=1.0,
            sale_fee=0.1,
            shipping=0.1,
            usd_to_jpy_rate=150.0,
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


def test_set_if_value_do_set() -> None:
    input_dict: dict[str, int] = {}
    key = 'a'
    value = 1
    schemas.set_if_value(input_dict, key, value)
    assert input_dict[key] == value


@pytest.mark.parametrize(
    ('value'),
    [
        pytest.param(None, id='none_value'),
        pytest.param('', id='empty_string'),
        pytest.param([], id='empty_list'),
        pytest.param({}, id='empty_dict'),
    ],
)
def test_set_if_value_no_set(value: str | list[object] | dict[str, object] | None) -> None:
    input_dict = {}
    key = 'a'
    schemas.set_if_value(input_dict, key, value)
    assert len(input_dict) == 0
