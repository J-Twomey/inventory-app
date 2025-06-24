from collections.abc import Sequence

from sqlalchemy import (
    and_,
    select,
)
from sqlalchemy.orm import Session

from .models import Item
from .schemas import (
    ItemCreate,
    ItemSearch,
    ItemUpdate,
)


def create_item(
        db: Session,
        item: ItemCreate,
) -> Item:
    item_data = item.model_dump(
        exclude={
            'grading_fee_total',
            'total_cost',
            'total_fees',
            'return_usd',
            'return_jpy',
            'net_jpy',
            'net_percent',
        },
    )
    grading_fee_total = sum(item.grading_fee.values())
    db_item = Item(**item_data, grading_fee_total=grading_fee_total)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_item(
        db: Session,
        item_id: int,
) -> Item | None:
    return db.query(Item).filter(Item.id == item_id).first()


def get_newest_items(
        db: Session,
        skip: int = 0,
        limit: int = 100,
) -> list[Item]:
    items = db.query(Item).order_by(Item.id.desc()).offset(skip).limit(limit).all()
    return list(reversed(items))


def delete_item_by_id(
        db: Session,
        item_id: int,
) -> bool:
    item = get_item(db, item_id)
    if item is None:
        return False
    db.delete(item)
    db.commit()
    return True


def search_for_items(
        db: Session,
        search_params: ItemSearch,
) -> Sequence[Item]:
    search_values = search_params.model_dump(exclude_unset=True)

    filters = []
    for field, value in search_values.items():
        if value is None or value == []:
            continue

        if field == 'qualifiers':
            enum_values = [q.value for q in value]

            for val in enum_values:
                filters.append(Item.qualifiers.contains([val]))
        elif field == 'submission_number':
            raise NotImplementedError
        else:
            column = getattr(Item, field)
            filters.append(column == value)

    statement = select(Item).where(and_(*filters))
    result = db.execute(statement)
    return result.scalars().all()


def edit_item(
        db: Session,
        item_id: int,
        item_update: ItemUpdate,
) -> int:
    item = get_item(db, item_id)
    if item is None:
        return 404
    update_data = item_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)

    if 'grading_fee' in update_data:
        item.grading_fee_total = sum(item.grading_fee.values())

    db.commit()
    db.refresh(item)
    return 303
