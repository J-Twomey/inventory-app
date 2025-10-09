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
    if item.intent != desired.value:
        raise ValueError(
            f'Item {item.id} intent field is required to be set to {desired.name}, but is '
            f'currently set to {Intent(item.intent).name}'
        )


def check_status(
        item: Item,
        desired: Status,
) -> None:
    if item.status != desired.value:
        raise ValueError(
            f'Item {item.id} status field is required to be set to {desired.name}, but is '
            f'currently set to {Status(item.status).name}'
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
        )
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
