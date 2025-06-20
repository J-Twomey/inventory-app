from datetime import date

from sqlalchemy.orm import Session

import src.crud as crud
import src.item_enums as item_enums
from .conftest import ItemFactory


def test_create_item_all_nullables_none(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item = item_factory.get()
    db_item = crud.create_item(db_session, item)
    assert db_item.id is not None
    assert db_item.name == 'TESTER'


def test_create_item_all_nullables_provided(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item = item_factory.get(
        qualifiers=[item_enums.Qualifier.UNLIMITED],
        details='Mint',
        grading_fee={1: 600, 2: 399},
        grade=10.,
        grading_company=item_enums.GradingCompany.PSA,
        cert=123456789,
        submission_number=[1, 2],
        list_price=500.,
        list_type=item_enums.ListingType.FIXED,
        list_date=date(2025, 10, 10),
        sale_total=550.,
        sale_date=date(2025, 10, 11),
        shipping=25.,
        sale_fee=25.,
        usd_to_jpy_rate=150.0,
    )
    db_item = crud.create_item(db_session, item)
    assert db_item.id is not None
    assert db_item.name == 'TESTER'
    assert db_item.grading_fee_total == 999


def test_get_item_returns_correct_item(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item = item_factory.get(name='GET_ITEM_TEST_ITEM')
    db_item = crud.create_item(db_session, item)
    result = crud.get_item(db_session, db_item.id)
    assert result is not None
    assert result.id == db_item.id
    assert result.name == 'GET_ITEM_TEST_ITEM'


def test_get_item_no_item(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item = item_factory.get(name='GET_ITEM_TEST_NO_ITEM')
    db_item = crud.create_item(db_session, item)
    result = crud.get_item(db_session, db_item.id + 1)
    assert result is None


def test_get_items_return_all_items(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item_names = ['one', 'two', 'three']
    items = [item_factory.get(n) for n in item_names]
    ids = []
    for item in items:
        db_item = crud.create_item(db_session, item)
        ids.append(db_item.id)
    result = crud.get_newest_items(db_session, skip=0, limit=100)
    result_ids = [r.id for r in result]
    result_names = [r.name for r in result]
    assert len(result) == len(item_names)
    assert result_ids == ids
    assert result_names == item_names


def test_get_items_skip_newest_item(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item_names = ['one', 'two', 'three']
    items = [item_factory.get(n) for n in item_names]
    ids = []
    for item in items:
        db_item = crud.create_item(db_session, item)
        ids.append(db_item.id)
    result = crud.get_newest_items(db_session, skip=1, limit=100)
    result_ids = [r.id for r in result]
    result_names = [r.name for r in result]
    assert len(result) == len(item_names) - 1
    assert result_ids == ids[:-1]
    assert result_names == item_names[:-1]


def test_get_items_take_two_items(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item_names = ['one', 'two', 'three']
    items = [item_factory.get(n) for n in item_names]
    ids = []
    for item in items:
        db_item = crud.create_item(db_session, item)
        ids.append(db_item.id)
    result = crud.get_newest_items(db_session, skip=0, limit=2)
    result_ids = [r.id for r in result]
    result_names = [r.name for r in result]
    assert len(result) == len(item_names) - 1
    assert result_ids == ids[1:]
    assert result_names == item_names[1:]


def test_get_items_skip_all_items(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item_names = ['one', 'two', 'three']
    items = [item_factory.get(n) for n in item_names]
    for item in items:
        crud.create_item(db_session, item)
    result = crud.get_newest_items(db_session, skip=3, limit=100)
    assert len(result) == 0


def test_get_items_no_items(db_session: Session) -> None:
    result = crud.get_newest_items(db_session, skip=0, limit=100)
    assert len(result) == 0


def test_delete_item_by_id_success(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item_names = ['one', 'two']
    items = [item_factory.get(n) for n in item_names]
    ids = []
    for item in items:
        db_item = crud.create_item(db_session, item)
        ids.append(db_item.id)
    result = crud.delete_item_by_id(db_session, ids[-1])
    assert result is True
    assert crud.get_item(db_session, ids[-1]) is None
    assert crud.get_item(db_session, ids[0]) is not None


def test_delete_item_by_id_failure(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item_names = ['one', 'two']
    items = [item_factory.get(n) for n in item_names]
    ids = []
    for item in items:
        db_item = crud.create_item(db_session, item)
        ids.append(db_item.id)
    result = crud.delete_item_by_id(db_session, ids[-1] + 1)
    assert result is False
    for id in ids:
        assert crud.get_item(db_session, id) is not None
