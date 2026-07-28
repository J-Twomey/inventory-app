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


def check_valid_merged_item_state(
    item: Item,
    item_update: ItemUpdate,
) -> None:
    merged = {f: getattr(item, f) for f in ItemCreate.model_fields}
    merged.update(item_update.to_model_kwargs())
    # mirror perform_item_update, which overwrites qualifiers even with an empty list
    merged['qualifiers'] = item_update.qualifiers
    ItemCreate(**merged)


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
    merged = {f: getattr(submission, f) for f in SubmissionBase.model_fields}
    merged[field] = update_value
    SubmissionBase(**merged)


def check_valid_grading_record_update(
    record: GradingRecord,
    update: GradingRecordUpdate,
) -> None:
    if all(
        (
            record.grading_fee is None,
            record.grade is None,
            record.cert is None,
        ),
    ):
        changes = (
            update.grading_fee is not None,
            update.grade is not None,
            update.cert is not None,
        )
        if any(changes) and not all(changes):
            raise ValueError(
                'Adding grading info to a record requires all of grading fee, grade, and cert',
            )
