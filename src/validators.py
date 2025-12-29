from .item_enums import (
    Intent,
    Status,
)
from .models import (
    GradingRecord,
    Item,
)
from .schemas import GradingRecordUpdate


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
    elif update_intent is not None and update_status is None:
        if current_status not in update_intent.allowed_statuses:
            raise ValueError(
                f'Cannot update item with status of {current_status.name} to have intent of '
                f'{update_intent.name}',
            )
    elif update_intent is None and update_status is not None:
        if update_status not in current_intent.allowed_statuses:
            raise ValueError(
                f'Cannot update item with intent of {current_intent.name} to have status of '
                f'{update_status.name}',
            )
    elif update_intent is not None and update_status is not None:
        if update_status not in update_intent.allowed_statuses:
            raise ValueError(
                f'Cannot update item to have intent of {update_intent.name} and status of '
                f'{update_status.name}',
            )


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
                'Updating a record from graded to graded requires setting all of grading_fee, '
                'grade, and cert',
            )
