from collections.abc import Callable
from datetime import date

import pytest

from src import (
    item_enums,
    validators,
)
from src.models import Item
from src.schemas import (
    GradingRecordUpdate,
    ItemUpdate,
)

from .conftest import (
    GradingRecordFactory,
    ItemCreateFactory,
    ItemFactory,
    SubmissionFactory,
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


def test_check_no_duplicate_items_in_submission_no_duplicate() -> None:
    item_ids = [1, 2, 3]
    validators.check_no_duplicate_items_in_submission(item_ids)


def test_check_no_duplicate_items_in_submission_has_duplicate() -> None:
    item_ids = [1, 2, 1]
    with pytest.raises(
        ValueError,
        match='Cannot add the same item to a submission more than once',
    ):
        validators.check_no_duplicate_items_in_submission(item_ids)


def test_check_required_fields_not_removed_no_removal() -> None:
    update = ItemUpdate.model_validate({'name': 'Golem', 'purchase_grade': ''})
    validators.check_required_fields_not_removed(update)


def test_check_required_fields_not_removed_removal_rejected() -> None:
    update = ItemUpdate.model_validate({'name': '', 'purchase_price': ''})
    with pytest.raises(ValueError, match='The following fields cannot be removed'):
        validators.check_required_fields_not_removed(update)


def test_check_status_change_to_submitted_valid_pending(
    item_with_submissions_factory: Callable[..., Item],
) -> None:
    item = item_with_submissions_factory()
    validators.check_status_change_to_submitted_valid(item)


def test_check_status_change_to_submitted_valid_no_records(
    item_factory: ItemFactory,
) -> None:
    item = item_factory.get()
    with pytest.raises(ValueError, match='can only be set to SUBMITTED by adding it'):
        validators.check_status_change_to_submitted_valid(item)


def test_check_status_change_to_submitted_valid_already_graded(
    item_with_submissions_factory: Callable[..., Item],
) -> None:
    item = item_with_submissions_factory(grading_fees=[1000], grades=[9.0], certs=[12345])
    with pytest.raises(
        ValueError,
        match='An item can only be set to SUBMITTED by adding it to a submission',
    ):
        validators.check_status_change_to_submitted_valid(item)


def test_check_status_change_to_submitted_valid_cracked_item(
    item_with_submissions_factory: Callable[..., Item],
) -> None:
    item = item_with_submissions_factory(is_cracked_flags=[True])
    with pytest.raises(
        ValueError,
        match='An item can only be set to SUBMITTED by adding it to a submission',
    ):
        validators.check_status_change_to_submitted_valid(item)


def test_check_new_item_not_submitted_is_not_submitted(
    item_create_factory: ItemCreateFactory,
) -> None:
    validators.check_new_item_not_submitted(item_create_factory.get())


def test_check_new_item_not_submitted_is_submitted(
    item_create_factory: ItemCreateFactory,
) -> None:
    item = item_create_factory.get(
        status=item_enums.Status.SUBMITTED,
        intent=item_enums.Intent.GRADE,
    )
    with pytest.raises(ValueError, match='cannot be created with a status of SUBMITTED'):
        validators.check_new_item_not_submitted(item)


def test_check_valid_submission_field_update_clearing_required_field(
    submission_factory: SubmissionFactory,
) -> None:
    submission = submission_factory.get()
    with pytest.raises(ValueError, match='Submission number cannot be empty'):
        validators.check_valid_submission_field_update(submission, 'submission_number', None)


def test_check_valid_submission_field_update_clearing_nullable_field(
    submission_factory: SubmissionFactory,
) -> None:
    submission = submission_factory.get(return_date=date(2025, 6, 1))
    validators.check_valid_submission_field_update(submission, 'return_date', None)


def test_check_valid_submission_field_update_invalid_date_order(
    submission_factory: SubmissionFactory,
) -> None:
    submission = submission_factory.get(submission_date=date(2025, 6, 1))
    with pytest.raises(ValueError, match='Return date cannot be before submission date'):
        validators.check_valid_submission_field_update(
            submission,
            'return_date',
            date(2025, 5, 1),
        )
