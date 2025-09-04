from .item_enums import (
    Intent,
    Status,
)
from .models import Item


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
