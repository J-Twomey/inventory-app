import pytest
from datetime import date
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
    import_fee = 100
    expected_total_cost = 685
    item = item_base_factory.get(
        purchase_price=purchase_price,
        import_fee=import_fee,
        grading_fee=grading_fees,
    )
    assert item.total_cost == expected_total_cost


def test_item_base_total_fees_no_sale(item_base_factory: ItemBaseFactory) -> None:
    item = item_base_factory.get(status=item_enums.Status.STORAGE)
    assert item.total_fees is None


def test_item_base_total_fees_with_sale(item_base_factory: ItemBaseFactory) -> None:
    item = item_base_factory.get(
        status=item_enums.Status.CLOSED,
        list_type=item_enums.ListingType.FIXED,
        sale_date=date(2025, 5, 6),
        sale_total=100.,
        shipping=5.5,
        sale_fee=8.7,
        usd_to_jpy_rate=150.,
    )
    expected_total = 14.2
    assert item.total_fees == expected_total


def test_item_base_return_usd_no_sale(item_base_factory: ItemBaseFactory) -> None:
    item = item_base_factory.get(status=item_enums.Status.STORAGE)
    assert item.return_usd is None


@pytest.mark.parametrize(
    ('sale_total', 'shipping', 'sale_fee', 'expected_return'),
    (
        pytest.param(15.31, 5.54, 8.66, 1.11, id='net_positive'),
        pytest.param(10.35, 5.54, 8.66, -3.85, id='net_negative'),
    ),
)
def test_item_base_return_usd_with_sale(
        item_base_factory: ItemBaseFactory,
        sale_total: float,
        shipping: float,
        sale_fee: float,
        expected_return: float,
) -> None:
    item = item_base_factory.get(
        status=item_enums.Status.CLOSED,
        list_type=item_enums.ListingType.FIXED,
        sale_date=date(2025, 5, 5),
        sale_total=sale_total,
        shipping=shipping,
        sale_fee=sale_fee,
        usd_to_jpy_rate=150.,
    )
    assert item.return_usd == expected_return


def test_item_base_return_jpy_no_sale(item_base_factory: ItemBaseFactory) -> None:
    item = item_base_factory.get(status=item_enums.Status.STORAGE)
    assert item.return_jpy is None


@pytest.mark.parametrize(
    ('sale_total', 'shipping', 'sale_fee', 'usd_to_jpy_rate', 'expected_return'),
    (
        pytest.param(9.64, 3.21, 2.87, 140.55, 500, id='net_positive'),
        pytest.param(5.49, 3.27, 2.99, 140.55, -108, id='net_negative'),
    ),
)
def test_item_base_return_jpy(
        item_base_factory: ItemBaseFactory,
        sale_total: float,
        shipping: float,
        sale_fee: float,
        usd_to_jpy_rate: float,
        expected_return: int,
) -> None:
    item = item_base_factory.get(
        status=item_enums.Status.CLOSED,
        list_type=item_enums.ListingType.FIXED,
        sale_date=date(2025, 5, 5),
        sale_total=sale_total,
        shipping=shipping,
        sale_fee=sale_fee,
        usd_to_jpy_rate=usd_to_jpy_rate,
    )
    assert item.return_jpy == expected_return


def test_item_base_net_jpy_no_sale(item_base_factory: ItemBaseFactory) -> None:
    item = item_base_factory.get(status=item_enums.Status.STORAGE)
    assert item.net_jpy is None


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
        pytest.param(10, {1: 100}, 9.64, 3.21, 2.87, 140.55, 390, id='net_positive'),
        pytest.param(1000, {1: 100}, 9.64, 3.21, 2.87, 140.55, -600, id='positive_ret_net_neg'),
        pytest.param(10, {1: 100}, 5.49, 3.27, 2.99, 140.55, -218, id='negative_ret_net_neg'),
    ),
)
def test_item_base_net_jpy(
        item_base_factory: ItemBaseFactory,
        purchase_price: int,
        grading_fees: dict[int, int],
        sale_total: float,
        shipping: float,
        sale_fee: float,
        usd_to_jpy_rate: float,
        expected_net: int,
) -> None:
    item = item_base_factory.get(
        status=item_enums.Status.CLOSED,
        list_type=item_enums.ListingType.FIXED,
        purchase_price=purchase_price,
        grading_fee=grading_fees,
        sale_date=date(2025, 5, 5),
        sale_total=sale_total,
        shipping=shipping,
        sale_fee=sale_fee,
        usd_to_jpy_rate=usd_to_jpy_rate,
    )
    assert item.net_jpy == expected_net


def test_item_base_net_percent_no_sale(item_base_factory: ItemBaseFactory) -> None:
    item = item_base_factory.get(status=item_enums.Status.STORAGE)
    assert item.net_percent is None


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
        pytest.param(10, {1: 100}, 9.64, 3.21, 2.87, 140.55, 354.55, id='net_positive'),
        pytest.param(1000, {1: 100}, 9.64, 3.21, 2.87, 140.55, -54.55, id='positive_ret_net_neg'),
        pytest.param(10, {1: 100}, 5.49, 3.27, 2.99, 140.55, -198.18, id='negative_ret_net_neg'),
    ),
)
def test_item_base_net_percent(
        item_base_factory: ItemBaseFactory,
        purchase_price: int,
        grading_fees: dict[int, int],
        sale_total: float,
        shipping: float,
        sale_fee: float,
        usd_to_jpy_rate: float,
        expected_percent: float,
) -> None:
    item = item_base_factory.get(
        status=item_enums.Status.CLOSED,
        list_type=item_enums.ListingType.FIXED,
        purchase_price=purchase_price,
        grading_fee=grading_fees,
        sale_date=date(2025, 5, 5),
        sale_total=sale_total,
        shipping=shipping,
        sale_fee=sale_fee,
        usd_to_jpy_rate=usd_to_jpy_rate,
    )
    assert item.net_percent == expected_percent


def test_item_base_required_field_not_allowed_as_empty_string(
        item_base_factory: ItemBaseFactory,
) -> None:
    with pytest.raises(ValidationError) as e:
        item_base_factory.get(name='')
    error_msg = e.value.errors()[0]['msg']
    assert 'Input should be a valid string' in error_msg


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
        pytest.param('cracked_from', [1, 2], [1, 2], id='excluded_field'),
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
    assert 'qualifiers must be provided as str or list[Qualifier]' in error_msg


@pytest.mark.parametrize(
    ('input_value', 'expected_value'),
    (
        pytest.param('', [], id='empty_string'),
        pytest.param([], [], id='empty_list'),
        pytest.param('4,5,6', [4, 5, 6], id='str_input'),
        pytest.param([3, 4, 5], [3, 4, 5], id='list_input'),
    ),
)
def test_item_base_parse_cracked_from_validator(
        item_base_factory: ItemBaseFactory,
        input_value: str | list[int],
        expected_value: list[int],
) -> None:
    item = item_base_factory.get(cracked_from=input_value)  # type: ignore[arg-type]
    actual_value = item.cracked_from
    assert actual_value == expected_value


def test_item_base_parse_cracked_from_wrong_type_input(item_base_factory: ItemBaseFactory) -> None:
    with pytest.raises(ValidationError) as e:
        item_base_factory.get(cracked_from=5)  # type: ignore[arg-type]
    error_msg = e.value.errors()[0]['msg']
    assert 'cracked_from must be provided as str or list[int]' in error_msg


@pytest.mark.parametrize(
    ('input_value', 'expected_value'),
    (
        pytest.param({}, {}, id='empty_dict'),
        pytest.param('{"1":"10","2":"20"}', {1: 10, 2: 20}, id='str_input'),
        pytest.param({1: 10, 2: 20}, {1: 10, 2: 20}, id='dict_input'),
    ),
)
def test_item_base_parse_grading_fee_validator(
        item_base_factory: ItemBaseFactory,
        input_value: str | dict[int, int],
        expected_value: dict[int, int],
) -> None:
    item = item_base_factory.get(grading_fee=input_value)  # type: ignore[arg-type]
    actual_value = item.grading_fee
    assert actual_value == expected_value


def test_item_base_parse_grading_fee_invalid_json_input(
        item_base_factory: ItemBaseFactory,
) -> None:
    with pytest.raises(ValidationError) as e:
        item_base_factory.get(grading_fee='')  # type: ignore[arg-type]
    error_msg = e.value.errors()[0]['msg']
    assert 'grading_fee must be valid JSON' in error_msg


def test_item_base_parse_grading_fee_wrong_type_input(
        item_base_factory: ItemBaseFactory,
) -> None:
    with pytest.raises(ValidationError) as e:
        item_base_factory.get(grading_fee=8)  # type: ignore[arg-type]
    error_msg = e.value.errors()[0]['msg']
    assert 'grading_fee must be provided as str or dict[int, int]' in error_msg


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
        'listing date cannot be before purchase date (got listing date: 2025-05-04, '
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
        'sale date cannot be before listing date (got sale date: 2025-05-05, '
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
    assert "status CLOSED requires the following missing fields: ['sale_total']" in error_msg


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
    assert "status SUBMITTED requires the following fields to be null: ['list_date']" in error_msg


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


def test_appropriate_intent_no_error_is_listed(item_base_factory: ItemBaseFactory) -> None:
    item_base_factory.get(
        purchase_date=date(2025, 5, 5),
        status=item_enums.Status.LISTED,
        intent=item_enums.Intent.SELL,
        list_type=item_enums.ListingType.FIXED,
        list_date=date(2025, 5, 6),
        list_price=1.,
    )


def test_appropriate_intent_no_error_is_closed(item_base_factory: ItemBaseFactory) -> None:
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
    )


def test_appropriate_intent_no_error_intent_is_crack(item_base_factory: ItemBaseFactory) -> None:
    item_base_factory.get(
        purchase_date=date(2025, 5, 5),
        status=item_enums.Status.STORAGE,
        intent=item_enums.Intent.CRACK,
        grade=9.,
        grading_company=item_enums.GradingCompany.CGC,
        cert=1,
    )


def test_appropriate_intent_listed_error(item_base_factory: ItemBaseFactory) -> None:
    with pytest.raises(ValidationError) as e:
        item_base_factory.get(
            purchase_date=date(2025, 5, 5),
            status=item_enums.Status.LISTED,
            intent=item_enums.Intent.KEEP,
            list_type=item_enums.ListingType.FIXED,
            list_date=date(2025, 5, 6),
            list_price=1.,
        )
    error_msg = e.value.errors()[0]['msg']
    assert 'Item cannot be listed or closed without intent of SELL' in error_msg


def test_appropriate_intent_crack_error(item_base_factory: ItemBaseFactory) -> None:
    with pytest.raises(ValidationError) as e:
        item_base_factory.get(
            purchase_date=date(2025, 5, 5),
            status=item_enums.Status.STORAGE,
            intent=item_enums.Intent.CRACK,
            grade=9.,
            grading_company=item_enums.GradingCompany.RAW,
            cert=1,
        )
    error_msg = e.value.errors()[0]['msg']
    assert 'Item cannot have intent of CRACK without being graded' in error_msg


def test_check_required_fields_based_on_grading_company_no_error(
        item_base_factory: ItemBaseFactory,
) -> None:
    item_base_factory.get(
        purchase_date=date(2025, 5, 5),
        status=item_enums.Status.STORAGE,
        grading_company=item_enums.GradingCompany.PSA,
        grade=10.,
        cert=1,
    )


def test_check_required_fields_based_on_grading_company_error_case(
        item_base_factory: ItemBaseFactory,
) -> None:
    with pytest.raises(ValidationError) as e:
        item_base_factory.get(
            purchase_date=date(2025, 5, 5),
            status=item_enums.Status.STORAGE,
            grading_company=item_enums.GradingCompany.PSA,
            grade=10.,
            cert=None,
        )
    error_msg = e.value.errors()[0]['msg']
    assert "graded card requires the following missing fields: ['cert']" in error_msg


def test_check_required_null_fields_based_on_grading_company_no_error(
        item_base_factory: ItemBaseFactory,
) -> None:
    item_base_factory.get(
        purchase_date=date(2025, 5, 5),
        status=item_enums.Status.STORAGE,
    )


def test_check_required_null_fields_based_on_grading_company_error_case(
        item_base_factory: ItemBaseFactory,
) -> None:
    with pytest.raises(ValidationError) as e:
        item_base_factory.get(
            purchase_date=date(2025, 5, 5),
            status=item_enums.Status.STORAGE,
            grading_company=item_enums.GradingCompany.RAW,
            cert=1,
        )
    error_msg = e.value.errors()[0]['msg']
    assert "raw card can not have the following non null fields: ['cert']" in error_msg


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
