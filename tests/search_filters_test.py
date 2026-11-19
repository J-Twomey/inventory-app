from sqlalchemy.sql.operators import eq

from src import (
    item_enums,
    search_filters,
)

from .conftest import ItemFactory


def test_build_search_filters_no_special_case() -> None:
    params = {'name': 'Unown', 'set_name': 'Base Set'}
    filters, post_filters = search_filters.build_search_filters(params)

    assert filters[0].left.key == 'name'
    assert filters[0].right.value == 'Unown'
    assert filters[0].operator is eq
    assert filters[1].left.key == 'set_name'
    assert filters[1].right.value == 'Base Set'
    assert filters[1].operator is eq
    assert post_filters == []


def test_build_search_filters_grading_company_is_sql_filter() -> None:
    params = {'name': 'Unown', 'grading_company': item_enums.GradingCompany.PSA}
    filters, post_filters = search_filters.build_search_filters(params)

    assert filters[0].left.key == 'name'
    assert filters[0].right.value == 'Unown'
    assert filters[0].operator is eq
    assert len(filters) == 2
    assert post_filters == []


def test_build_search_filters_qualifiers_is_post_filter(
    item_factory: ItemFactory,
) -> None:
    params = {'qualifiers': [item_enums.Qualifier.FIRST_EDITION]}
    filters, post_filters = search_filters.build_search_filters(params)

    assert filters == []
    assert len(post_filters) == 1

    keep = post_filters[0]
    assert keep(item_factory.get(qualifiers=[item_enums.Qualifier.FIRST_EDITION]))
    assert keep(
        item_factory.get(
            qualifiers=[item_enums.Qualifier.FIRST_EDITION, item_enums.Qualifier.REVERSE_HOLO]
        )
    )
    assert not keep(item_factory.get(qualifiers=[]))
    assert not keep(item_factory.get(qualifiers=[item_enums.Qualifier.REVERSE_HOLO]))
