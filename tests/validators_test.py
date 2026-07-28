from datetime import date

import pytest

from src import (
    item_enums,
    validators,
)
from src.schemas import (
    GradingRecordUpdate,
    ItemUpdate,
)

from .conftest import (
    GradingRecordFactory,
    ItemFactory,
)


def test_check_valid_grading_record_update_already_graded(
    grading_record_factory: GradingRecordFactory,
) -> None:
    record = grading_record_factory.get(grading_fee=1000, grade=9.0, cert=10000)
    update = GradingRecordUpdate()
    validators.check_valid_grading_record_update(record, update)


def test_check_valid_grading_record_update_changes_ok(
    grading_record_factory: GradingRecordFactory,
) -> None:
    record = grading_record_factory.get(grading_fee=None, grade=None, cert=None)
    update = GradingRecordUpdate(grading_fee=100, grade=9.5, cert=12345)
    validators.check_valid_grading_record_update(record, update)


def test_check_valid_grading_record_update_changes_ng(
    grading_record_factory: GradingRecordFactory,
) -> None:
    record = grading_record_factory.get(grading_fee=None, grade=None, cert=None)
    update = GradingRecordUpdate(grading_fee=100, grade=9.5, cert=None)
    with pytest.raises(
        ValueError,
        match=('Adding grading info to a record requires all of grading fee, grade, and cert'),
    ):
        validators.check_valid_grading_record_update(record, update)


def test_check_valid_merged_item_state_ok(item_factory: ItemFactory) -> None:
    item = item_factory.get(
        status=item_enums.Status.LISTED,
        intent=item_enums.Intent.SELL,
        list_price=10.0,
        list_type=item_enums.ListingType.FIXED,
        list_date=date(2025, 6, 1),
    )
    update = ItemUpdate(
        status=item_enums.Status.CLOSED,
        sale_total=20.0,
        sale_date=date(2025, 6, 2),
        shipping=1.0,
        sale_fee=1.0,
        usd_to_jpy_rate=140.0,
    )
    validators.check_valid_merged_item_state(item, update)


def test_check_valid_merged_item_state_stale_listing_fields(item_factory: ItemFactory) -> None:
    item = item_factory.get(
        status=item_enums.Status.LISTED,
        intent=item_enums.Intent.SELL,
        list_price=10.0,
        list_type=item_enums.ListingType.FIXED,
        list_date=date(2025, 6, 1),
    )
    update = ItemUpdate(
        status=item_enums.Status.STORAGE,
        list_type=item_enums.ListingType.NO_LIST,
    )
    with pytest.raises(ValueError, match='requires the following fields to be null'):
        validators.check_valid_merged_item_state(item, update)


def test_check_valid_merged_item_state_date_conflict(item_factory: ItemFactory) -> None:
    item = item_factory.get(
        status=item_enums.Status.CLOSED,
        intent=item_enums.Intent.SELL,
        list_price=10.0,
        list_type=item_enums.ListingType.FIXED,
        list_date=date(2025, 6, 1),
        sale_total=20.0,
        sale_date=date(2025, 6, 2),
        shipping=1.0,
        sale_fee=1.0,
        usd_to_jpy_rate=140.0,
    )
    update = ItemUpdate(sale_date=date(2025, 5, 20))
    with pytest.raises(ValueError, match='Sale date cannot be before listing date'):
        validators.check_valid_merged_item_state(item, update)
