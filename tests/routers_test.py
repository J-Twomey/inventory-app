from collections.abc import Callable

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.models import Item

from .conftest import ItemFactory


def test_read_root(client: TestClient) -> None:
    response = client.get('/')
    assert response.status_code == 200


def test_view_items_no_items(client: TestClient) -> None:
    response = client.get('/items_view')
    assert response.status_code == 200


def test_view_items_shows_seeded_item(
    client: TestClient,
    db_session: Session,
    item_factory: ItemFactory,
) -> None:
    item = item_factory.get(name='SMOKE_TEST_ITEM')
    db_session.add(item)
    db_session.flush()

    response = client.get('/items_view')
    assert response.status_code == 200
    assert 'SMOKE_TEST_ITEM' in response.text


def test_submit_edit_item(
    client: TestClient,
    db_session: Session,
    item_factory: ItemFactory,
) -> None:
    item = item_factory.get(name='BEFORE_EDIT')
    db_session.add(item)
    db_session.flush()

    response = client.post(
        f'/edit/{item.id}',
        data={'name': 'AFTER_EDIT'},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers['location'] == '/items_view'
    assert item.name == 'AFTER_EDIT'


def test_submit_edit_grading_record(
    client: TestClient,
    item_with_submissions_factory: Callable[..., Item],
) -> None:
    item = item_with_submissions_factory(
        grading_fees=[10],
        grades=[9.0],
        certs=[111],
        is_cracked_flags=[False],
    )
    record = item.submissions[0]

    form_page = client.get(f'/grading_record_edit/{record.id}')
    assert form_page.status_code == 200

    response = client.post(
        f'/grading_record_edit/{record.id}',
        data={'grading_fee': '25', 'grade': '9.5', 'cert': '', 'is_cracked': 'on'},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert record.grading_fee == 25
    assert record.grade == 9.5
    # An empty form field means untouched, not cleared
    assert record.cert == 111
    assert record.is_cracked is True


def test_submit_edit_grading_record_unchecked_checkbox_clears_is_cracked(
    client: TestClient,
    item_with_submissions_factory: Callable[..., Item],
) -> None:
    item = item_with_submissions_factory(
        grading_fees=[10],
        grades=[9.0],
        certs=[111],
        is_cracked_flags=[True],
    )
    record = item.submissions[0]

    # Browsers omit unchecked checkboxes from the form body entirely
    response = client.post(
        f'/grading_record_edit/{record.id}',
        data={'grading_fee': '', 'grade': '', 'cert': ''},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert record.is_cracked is False
