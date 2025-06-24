from datetime import date

import pytest
from sqlalchemy.orm import Session

import src.crud as crud
import src.item_enums as item_enums
import src.models as models
import src.schemas as schemas
from .conftest import ItemFactory


def test_create_item_all_nullables_none(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item = item_factory.get()
    db_item = crud.create_item(db_session, item)
    item_from_db = db_session.query(models.Item).first()
    assert db_item.id is not None and db_item == item_from_db
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
    item_from_db = db_session.query(models.Item).first()
    assert db_item.id is not None and db_item == item_from_db
    assert db_item.name == 'TESTER'
    assert db_item.grading_fee_total == 999


def test_create_item_multiple_qualifiers(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    input_qualifiers = [item_enums.Qualifier.REVERSE_HOLO, item_enums.Qualifier.CRYSTAL]
    item = item_factory.get(
        qualifiers=input_qualifiers,
    )
    db_item = crud.create_item(db_session, item)
    item_from_db = db_session.query(models.Item).first()
    assert db_item.id is not None and db_item == item_from_db
    assert db_item.qualifiers == input_qualifiers


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
    items = [item_factory.get(name=n) for n in item_names]
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
    items = [item_factory.get(name=n) for n in item_names]
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
    items = [item_factory.get(name=n) for n in item_names]
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
    items = [item_factory.get(name=n) for n in item_names]
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
    items = [item_factory.get(name=n) for n in item_names]
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
    items = [item_factory.get(name=n) for n in item_names]
    ids = []
    for item in items:
        db_item = crud.create_item(db_session, item)
        ids.append(db_item.id)
    result = crud.delete_item_by_id(db_session, ids[-1] + 1)
    assert result is False
    for id in ids:
        assert crud.get_item(db_session, id) is not None


def test_search_for_items_no_filters(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item_names = ['one', 'two']
    items = [item_factory.get(name=n) for n in item_names]
    for item in items:
        crud.create_item(db_session, item)
    search_params = schemas.ItemSearchForm().to_item_search()
    result = crud.search_for_items(db_session, search_params)
    assert len(result) == 2


def test_search_for_items_simple_case(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item_names = ['one', 'two']
    items = [item_factory.get(name=n) for n in item_names]
    for item in items:
        crud.create_item(db_session, item)
    search_params = schemas.ItemSearchForm(name='two').to_item_search()
    result = crud.search_for_items(db_session, search_params)
    assert len(result) == 1
    assert result[0].name == 'two'


def test_search_for_items_multiple_search_criteria(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item_grading_companies = [
        item_enums.GradingCompany.RAW,
        item_enums.GradingCompany.PSA,
        item_enums.GradingCompany.PSA,
        item_enums.GradingCompany.PSA,
    ]
    item_languages = [
        item_enums.Language.KOREAN,
        item_enums.Language.KOREAN,
        item_enums.Language.KOREAN,
        item_enums.Language.GERMAN,
    ]
    items = [
        item_factory.get(grading_company=gc, language=lang) for gc, lang in zip(
            item_grading_companies,
            item_languages,
        )
    ]
    for item in items:
        crud.create_item(db_session, item)
    search_params = schemas.ItemSearchForm(
        language='KOREAN',
        grading_company='PSA',
    ).to_item_search()
    result = crud.search_for_items(db_session, search_params)
    assert len(result) == 2
    assert all(
        getattr(r, field_name) == fv for r, field_name, fv in zip(
            result,
            ('language', 'grading_company'),
            (item_enums.Language.KOREAN, item_enums.GradingCompany.PSA),
        )
    )


@pytest.mark.xfail
def test_search_for_items_multiple_qualifiers(
        db_session: Session,
        item_factory: ItemFactory,
) -> None:
    item_qualifiers = [
        [item_enums.Qualifier.NON_HOLO],
        [item_enums.Qualifier.NON_HOLO, item_enums.Qualifier.CRYSTAL],
        [item_enums.Qualifier.FIRST_EDITION],
        [item_enums.Qualifier.CRYSTAL],
        [],
    ]
    items = [item_factory.get(qualifiers=q) for q in item_qualifiers]
    for item in items:
        crud.create_item(db_session, item)
    search_params = schemas.ItemSearchForm(qualifiers=['NON_HOLO', 'CRYSTAL']).to_item_search()
    result = crud.search_for_items(db_session, search_params)
    assert len(result) == 1
    assert result[0].qualifiers == [item_enums.Qualifier.NON_HOLO, item_enums.Qualifier.CRYSTAL]
