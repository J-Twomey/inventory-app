from typing import (
    Any,
    Protocol,
)

from pydantic import (
    BaseModel,
    ValidationError,
)

from .item_enums import (
    Intent,
    Status,
)
from .models import (
    GradingRecord,
    Item,
    Submission,
)
from .schemas import (
    GradingRecordUpdate,
    ItemCreate,
    ItemUpdate,
    SubmissionBase,
)

GRADING_INFO_FIELDS = ('grading_fee', 'grade', 'cert')


def check_intent(
    item: Item,
    desired: Intent,
) -> None:
    if item.intent != desired:
        raise ValueError(
            f'Item {item.id} intent field is required to be set to {desired.name}, but is '
            f'currently set to {item.intent.name}',
        )


def check_status(
    item: Item,
    desired: Status,
) -> None:
    if item.status != desired:
        raise ValueError(
            f'Item {item.id} status field is required to be set to {desired.name}, but is '
            f'currently set to {item.status.name}',
        )


def check_valid_intent_or_status_update(
    current_intent: Intent,
    current_status: Status,
    update_intent: Intent | None,
    update_status: Status | None,
) -> None:
    if update_intent is None and update_status is None:
        return
    if (
        update_intent is not None
        and update_status is None
        and current_status not in update_intent.allowed_statuses
    ):
        raise ValueError(
            f'Cannot update item with status of {current_status.name} to have intent of '
            f'{update_intent.name}',
        )
    if (
        (update_intent is None)
        and update_status is not None
        and update_status not in current_intent.allowed_statuses
    ):
        raise ValueError(
            f'Cannot update item with intent of {current_intent.name} to have status of '
            f'{update_status.name}',
        )
    if (
        update_intent is not None
        and update_status is not None
        and update_status not in update_intent.allowed_statuses
    ):
        raise ValueError(
            f'Cannot update item to have intent of {update_intent.name} and status of '
            f'{update_status.name}',
        )
    if current_status == Status.SUBMITTED and update_status is not None:
        raise ValueError(
            'Cannot update an item status if it is SUBMITTED (use the grading record page)',
        )


def check_status_change_to_submitted_valid(item: Item) -> None:
    """A status change to SUBMITTED should only be valid if there is an open grading record"""
    if not any(record.grade is None and not record.is_cracked for record in item.submissions):
        raise ValueError('An item can only be set to SUBMITTED by adding it to a submission')


def check_new_item_not_submitted(item: ItemCreate) -> None:
    if item.status == Status.SUBMITTED:
        raise ValueError('A new item cannot be created with a status of SUBMITTED')


class SupportsModelKwargs(Protocol):
    def to_model_kwargs(self) -> dict[str, Any]: ...


def check_required_fields_not_removed(
    update: SupportsModelKwargs,
    create_schema: type[BaseModel],
) -> None:
    update_data = update.to_model_kwargs()
    removed = [
        field
        for field, info in create_schema.model_fields.items()
        if info.is_required() and field in update_data and update_data[field] is None
    ]
    if removed:
        raise ValueError(f'The following fields cannot be removed: {removed}')


def check_item_valid_after_update(
    item: Item,
    item_update: ItemUpdate,
) -> None:
    merged = {f: getattr(item, f) for f in ItemCreate.model_fields}
    merged.update(item_update.to_model_kwargs())
    try:
        ItemCreate(**merged)
    except ValidationError as e:
        # Unwrap pydantic's report
        reasons = '; '.join(err['msg'].removeprefix('Value error, ') for err in e.errors())
        raise ValueError(reasons) from None


def check_no_duplicate_items_in_submission(item_ids: list[int]) -> None:
    duplicate_ids = sorted({i for i in item_ids if item_ids.count(i) > 1})
    if duplicate_ids:
        joined = ', '.join(str(i) for i in duplicate_ids)
        raise ValueError(
            f'Cannot add the same item to a submission more than once (item {joined})',
        )


def check_valid_submission_field_update(
    submission: Submission,
    field: str,
    update_value: object,
) -> None:
    column = Submission.__table__.columns.get(field)
    if column is not None and not column.nullable and update_value is None:
        raise ValueError(f'{field.replace("_", " ").capitalize()} cannot be empty')

    merged = {f: getattr(submission, f) for f in SubmissionBase.model_fields}
    merged[field] = update_value
    SubmissionBase(**merged)


def check_valid_grading_record_update(
    record: GradingRecord,
    update: GradingRecordUpdate,
) -> None:
    update_data = update.to_model_kwargs()
    merged = [
        update_data.get(field, getattr(record, field)) is not None for field in GRADING_INFO_FIELDS
    ]
    if any(merged) and not all(merged):
        raise ValueError(
            'A grading record requires grading fee, grade, and cert to all be set, or all be none',
        )


def check_older_record_stays_cracked(
    record: GradingRecord,
    update: GradingRecordUpdate,
    item: Item,
) -> None:
    latest_record = max(item.submissions, key=lambda s: s.submission_number)
    # check status of cracked after the edit is performed
    is_cracked_after_update = update.to_model_kwargs().get('is_cracked', record.is_cracked)
    if record is not latest_record and not is_cracked_after_update:
        raise ValueError(
            f'Grading record {record.id} is not the latest for item {item.id}, so it must stay '
            f'marked as cracked',
        )


def check_all_grading_records_are_cracked(item: Item) -> None:
    if any(not record.is_cracked for record in item.submissions):
        raise ValueError(
            f'Item {item.id} has a grading record that is not marked as cracked, so it cannot be '
            f'added to a new submission',
        )


def check_grade_intent_allowed(item: Item, intent: Intent | None) -> None:
    if intent != Intent.GRADE:
        return
    latest_record = max(item.submissions, key=lambda s: s.submission_number, default=None)
    if (
        latest_record is not None
        and latest_record.grade is not None
        and not latest_record.is_cracked
    ):
        raise ValueError(
            f'Item {item.id} has been graded, so it cannot have an intent of GRADE unless its '
            f'latest grading record is cracked',
        )


def check_item_can_return_to_submitted(item: Item) -> None:
    populated = [f for f in Status.SUBMITTED.required_to_be_null if getattr(item, f) is not None]
    if populated:
        raise ValueError(
            f'Cannot remove grading info: item {item.id} must have the following fields cleared '
            f'first: {populated}',
        )
