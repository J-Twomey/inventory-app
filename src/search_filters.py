from collections.abc import Callable
from typing import Any

from sqlalchemy.sql.elements import ColumnElement

from .item_enums import Qualifier
from .models import Item


def qualifiers_filter(qualifiers: list[Qualifier]) -> Callable[[Item], bool]:
    return lambda item: all(q in item.qualifiers for q in qualifiers)


def build_search_filters(
    search_params: dict[str, Any],
) -> tuple[list[ColumnElement[bool]], list[Callable[[Item], bool]]]:
    filters: list[ColumnElement[bool]] = []
    post_filters: list[Callable[[Item], bool]] = []
    for field, value in search_params.items():
        if value is None or value == []:
            continue

        if field == 'qualifiers':
            post_filters.append(qualifiers_filter(value))
        elif field.endswith('_min'):
            base_field = field.removesuffix('_min')
            column = getattr(Item, base_field)
            filters.append(column >= value)
        elif field.endswith('_max'):
            base_field = field.removesuffix('_max')
            column = getattr(Item, base_field)
            filters.append(column <= value)
        else:
            column = getattr(Item, field)
            filters.append(column == value)
    return filters, post_filters
