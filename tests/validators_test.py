from collections.abc import Callable
from datetime import date

import pytest
from pydantic import BaseModel

from src import (
    item_enums,
    validators,
)
from src.models import Item
from src.schemas import (
    GradingRecordUpdate,
    ItemCreate,
    ItemUpdate,
    RefundCreate,
    RefundUpdate,
    RemunerationCreate,
    RemunerationUpdate,
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
        match=(
            'A grading record requires grading fee, grade, and cert to all be set, or all be none'
        ),
    ):
        validators.check_valid_grading_record_update(record, update)


def test_check_valid_grading_record_update_full_removal_ok(
    grading_record_factory: GradingRecordFactory,
) -> None:
    record = grading_record_factory.get(grading_fee=1000, grade=9.0, cert=10000)
    update = GradingRecordUpdate.model_validate({'grading_fee': '', 'grade': '', 'cert': ''})
    validators.check_valid_grading_record_update(record, update)


@pytest.mark.parametrize(
    'form_data',
    [
        pytest.param(
            {'grading_fee': '1000', 'grade': '9.0', 'cert': ''},
            id='removes_cert',
        ),
        pytest.param(
            {'grading_fee': '1000', 'grade': '', 'cert': '10000'},
            id='removes_grade',
        ),
        pytest.param(
            {'grading_fee': '', 'grade': '9.0', 'cert': '10000'},
            id='removes_grading_fee',
        ),
        pytest.param(
            {'cert': ''},
            id='removes_cert_only_field_sent',
        ),
    ],
)
def test_check_valid_grading_record_update_partial_removal_ng(
    grading_record_factory: GradingRecordFactory,
    form_data: dict[str, str],
) -> None:
    record = grading_record_factory.get(grading_fee=1000, grade=9.0, cert=10000)
    update = GradingRecordUpdate.model_validate(form_data)
    with pytest.raises(
        ValueError,
        match=(
            'A grading record requires grading fee, grade, and cert to all be set, or all be none'
        ),
    ):
        validators.check_valid_grading_record_update(record, update)


def test_check_item_can_return_to_submitted_ok(item_factory: ItemFactory) -> None:
    item = item_factory.get(
        status=item_enums.Status.STORAGE,
        intent=item_enums.Intent.GRADE,
    )
    validators.check_item_can_return_to_submitted(item)


def test_check_item_can_return_to_submitted_ng_bad_intent(item_factory: ItemFactory) -> None:
    item = item_factory.get(
        status=item_enums.Status.STORAGE,
        intent=item_enums.Intent.SELL,
    )
    with pytest.raises(
        ValueError, match='has an intent of SELL, which does not allow a status of SUBMITTED'
    ):
        validators.check_item_can_return_to_submitted(item)


def test_check_item_can_return_to_submitted_ng_populated_fields(
    item_factory: ItemFactory,
) -> None:
    item = item_factory.get(
        status=item_enums.Status.LISTED,
        intent=item_enums.Intent.GRADE,
        list_price=2000.0,
        list_type=item_enums.ListingType.AUCTION,
        list_date=date(2026, 1, 1),
    )
    with pytest.raises(ValueError, match='must have the following fields cleared first'):
        validators.check_item_can_return_to_submitted(item)


def test_check_item_valid_after_update_ok(item_factory: ItemFactory) -> None:
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
    validators.check_item_valid_after_update(item, update)


def test_check_item_valid_after_update_stale_listing_fields(item_factory: ItemFactory) -> None:
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
        validators.check_item_valid_after_update(item, update)


def test_check_item_valid_after_update_date_conflict(item_factory: ItemFactory) -> None:
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
        validators.check_item_valid_after_update(item, update)


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


@pytest.mark.parametrize(
    ('update', 'create_schema'),
    [
        pytest.param(ItemUpdate(), ItemCreate, id='item'),
        pytest.param(RefundUpdate(), RefundCreate, id='refund'),
        pytest.param(RemunerationUpdate(), RemunerationCreate, id='remuneration'),
    ],
)
def test_check_required_fields_not_removed_no_changes(
    update: validators.SupportsModelKwargs,
    create_schema: type[BaseModel],
) -> None:
    validators.check_required_fields_not_removed(update, create_schema)


@pytest.mark.parametrize(
    ('update', 'create_schema'),
    [
        pytest.param(
            ItemUpdate.model_validate({'name': 'Golem', 'purchase_grade': ''}),
            ItemCreate,
            id='item_purchase_grade',
        ),
        pytest.param(RefundUpdate(item_id=None), RefundCreate, id='refund_item_id'),
        pytest.param(
            RemunerationUpdate(item_id=None),
            RemunerationCreate,
            id='remuneration_item_id',
        ),
    ],
)
def test_check_required_fields_not_removed_clearing_nullable_field(
    update: validators.SupportsModelKwargs,
    create_schema: type[BaseModel],
) -> None:
    validators.check_required_fields_not_removed(update, create_schema)


@pytest.mark.parametrize(
    ('update', 'create_schema'),
    [
        pytest.param(
            ItemUpdate.model_validate({'name': ''}),
            ItemCreate,
            id='item_name',
        ),
        pytest.param(
            ItemUpdate.model_validate({'name': '', 'purchase_price': ''}),
            ItemCreate,
            id='item_multiple_fields',
        ),
        pytest.param(
            RefundUpdate(refund_amount_usd=None),
            RefundCreate,
            id='refund_amount_usd',
        ),
        pytest.param(RefundUpdate(refund_date=None), RefundCreate, id='refund_date'),
        pytest.param(RefundUpdate(refund_reason=None), RefundCreate, id='refund_reason'),
        pytest.param(
            RefundUpdate(usd_to_jpy_rate=None),
            RefundCreate,
            id='refund_usd_to_jpy_rate',
        ),
        pytest.param(
            RemunerationUpdate(remuneration_amount_jpy=None),
            RemunerationCreate,
            id='remuneration_amount_jpy',
        ),
        pytest.param(
            RemunerationUpdate(remuneration_date=None),
            RemunerationCreate,
            id='remuneration_date',
        ),
        pytest.param(
            RemunerationUpdate(remuneration_source=None),
            RemunerationCreate,
            id='remuneration_source',
        ),
    ],
)
def test_check_required_fields_not_removed_raises_on_required_field_removal(
    update: validators.SupportsModelKwargs,
    create_schema: type[BaseModel],
) -> None:
    with pytest.raises(ValueError, match='The following fields cannot be removed'):
        validators.check_required_fields_not_removed(update, create_schema)


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
