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
    item_data = item.to_model_kwargs(
        exclude={
            'total_cost',
            'total_fees',
            'return_usd',
            'return_jpy',
            'net_jpy',
            'net_percent',
        },
    )
    db_item = Item(**item_data)
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
) -> Sequence[Item]:
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
    post_filters = []
    for field, value in search_values.items():
        if value is None or value == []:
            continue

        # Filter qualifiers and cracked_from after the sql search
        if field in ['qualifiers', 'cracked_from']:
            post_filters.append((field, value))
        elif field == 'submission_number':
            raise NotImplementedError
        else:
            column = getattr(Item, field)
            filters.append(column == value)

    statement = select(Item)
    if len(filters) > 0:
        statement = statement.where(and_(*filters))
    results = db.execute(statement).scalars().all()

    # Post filtering (for qualifiers and cracked_from)
    for field, value in post_filters:
        if field == 'qualifiers':
            qualifier_values = [q for q in value]
            results = [
                item for item in results
                if all(q in item.qualifiers for q in qualifier_values)
            ]
        elif field == 'cracked_from':
            results = [item for item in results if value in item.cracked_from]
    return results


def edit_item(
        db: Session,
        item_id: int,
        item_update: ItemUpdate,
) -> int:
    item = get_item(db, item_id)
    if item is None:
        return 404

    update_data = item_update.to_model_kwargs()
    # always add qualifiers even if it is an empty list
    update_data['qualifiers'] = item_update.qualifiers

    for key, value in update_data.items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)
    return 303


def get_all_submission_values(db: Session) -> list[int]:
    return [1, 2]
