from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

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
