from datetime import date
from typing import Any

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
    field_settings: dict[str, Any] = {
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


def test_submission_return_date_not_before_submission_date() -> None:
    schemas.SubmissionBase(
        submission_date=date(2026, 1, 10),
        return_date=date(2026, 1, 10),
    )


def test_submission_return_date_before_submission_date() -> None:
    with pytest.raises(ValidationError, match='Return date cannot be before submission date'):
        schemas.SubmissionBase(
            submission_date=date(2026, 1, 10),
            return_date=date(2026, 1, 5),
        )


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
    with pytest.raises(
        ValidationError,
        match='Item cannot have list_type of NO_LIST if listed or sold',
    ):
        item_base_factory.get(
            purchase_date=date(2025, 5, 5),
            status=item_enums.Status.LISTED,
            list_type=item_enums.ListingType.NO_LIST,
            list_date=date(2025, 5, 6),
            list_price=1.0,
        )


def test_appropriate_listing_type_storage_error(item_base_factory: ItemBaseFactory) -> None:
    with pytest.raises(
        ValidationError,
        match='Item cannot have a list_type other than NO_LIST if not listed or sold',
    ):
        item_base_factory.get(
            purchase_date=date(2025, 5, 5),
            status=item_enums.Status.STORAGE,
            list_type=item_enums.ListingType.FIXED,
        )


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
    with pytest.raises(
        ValidationError,
        match='Group discount cannot be assigned to an unsold item',
    ):
        item_base_factory.get(
            status=item_enums.Status.STORAGE,
            group_discount=True,
        )


def test_appropriate_audit_target_no_error(item_base_factory: ItemBaseFactory) -> None:
    item_base_factory.get(
        status=item_enums.Status.VAULT,
        audit_target=True,
    )


def test_appropriate_audit_target_listing_error(item_base_factory: ItemBaseFactory) -> None:
    with pytest.raises(
        ValidationError,
        match='Item assigned as an audit target can not be listed or closed',
    ):
        item_base_factory.get(
            purchase_date=date(2025, 5, 5),
            status=item_enums.Status.LISTED,
            intent=item_enums.Intent.SELL,
            list_type=item_enums.ListingType.AUCTION,
            list_date=date(2025, 5, 6),
            list_price=1.0,
            audit_target=True,
        )


def test_appropriate_audit_target_closed_error(item_base_factory: ItemBaseFactory) -> None:
    with pytest.raises(
        ValidationError,
        match='Item assigned as an audit target can not be listed or closed',
    ):
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
    with pytest.raises(
        ValidationError,
        match='Item can not have status of SUBMITTED with intent of SELL',
    ):
        item_create_factory.get(
            status=item_enums.Status.SUBMITTED,
            intent=item_enums.Intent.SELL,
        )


def test_item_create_parses_form_string_values() -> None:
    item = schemas.ItemCreate.model_validate(
        {
            'name': 'Golem',
            'set_name': 'Split Earth',
            'category': 'CARD',
            'language': 'JAPANESE',
            'qualifiers': ['UNLIMITED', 'CRYSTAL'],
            'details': '',
            'purchase_date': '2025-05-05',
            'purchase_price': '1000',
            'status': 'STORAGE',
            'intent': 'SELL',
            'import_fee': '0',
            'purchase_grading_company': 'RAW',
            'purchase_grade': '',
            'purchase_cert': '',
            'list_price': '',
            'list_type': 'NO_LIST',
            'list_date': '',
            'sale_total': '',
            'sale_date': '',
            'shipping': '',
            'sale_fee': '',
            'usd_to_jpy_rate': '',
            'object_variant': 'STANDARD',
            'audit_target': 'on',
        },
    )
    assert item.category == item_enums.Category.CARD
    assert item.language == item_enums.Language.JAPANESE
    assert item.qualifiers == [item_enums.Qualifier.UNLIMITED, item_enums.Qualifier.CRYSTAL]
    assert item.details is None
    assert item.purchase_date == date(2025, 5, 5)
    assert item.purchase_price == 1000
    assert item.purchase_grade is None
    assert item.audit_target is True
    assert item.group_discount is False


def test_item_create_qualifiers_default_to_empty(
    item_create_factory: ItemCreateFactory,
) -> None:
    item = item_create_factory.get()
    assert item.qualifiers == []


def test_item_update_treats_empty_values_as_unset() -> None:
    update = schemas.ItemUpdate.model_validate(
        {
            'name': 'Golem',
            'set_name': '',
            'status': 'STORAGE',
            'purchase_grade': '',
        },
    )
    assert update.to_model_kwargs() == {
        'name': 'Golem',
        'status': item_enums.Status.STORAGE,
        'group_discount': False,
        'audit_target': False,
        'cracked_from_purchase': False,
    }


def test_item_update_checked_checkbox_sets_true() -> None:
    update = schemas.ItemUpdate.model_validate({'audit_target': 'on'})
    assert update.audit_target is True
    assert update.group_discount is False
    assert update.cracked_from_purchase is False


def test_item_search_parses_query_string_values() -> None:
    search = schemas.ItemSearch.model_validate(
        {
            'name': 'Golem',
            'category': 'CARD',
            'language': 'JAPANESE',
            'qualifiers': ['UNLIMITED', 'CRYSTAL'],
            'grading_company': 'PSA',
            'purchase_date_min': '2025-05-05',
            'purchase_price_max': '1000',
            'cracked_from_purchase': 'true',
            'net_percent_min': '50',
        },
    )
    assert search.name == 'Golem'
    assert search.category == item_enums.Category.CARD
    assert search.language == item_enums.Language.JAPANESE
    assert search.qualifiers == [item_enums.Qualifier.UNLIMITED, item_enums.Qualifier.CRYSTAL]
    assert search.grading_company == item_enums.GradingCompany.PSA
    assert search.purchase_date_min == date(2025, 5, 5)
    assert search.purchase_price_max == 1000
    assert search.cracked_from_purchase is True
    assert search.net_percent_min == 50.0


def test_item_search_treats_empty_values_as_unset() -> None:
    search = schemas.ItemSearch.model_validate(
        {
            'name': '',
            'set_name': 'Jungle',
            'category': '',
            'purchase_price_min': '',
        },
    )
    assert search.model_dump(exclude_unset=True) == {'set_name': 'Jungle'}


def test_item_search_invalid_enum_name() -> None:
    with pytest.raises(ValidationError, match='Invalid Category: Bulbasaur'):
        schemas.ItemSearch.model_validate({'category': 'Bulbasaur'})
