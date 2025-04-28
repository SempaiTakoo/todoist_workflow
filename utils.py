from collections.abc import Callable, Sequence
from typing import TypeVar

T = TypeVar("T")


def find_by_predicate(items: Sequence[T], predicate: Callable[..., bool]) -> T | None:
    return next((item for item in items if predicate(item)), None)


def find_by_id(items: Sequence[T], item_id: str) -> T | None:
    return find_by_predicate(items, lambda x: x.id == item_id)


def find_by_name(items: Sequence[T], name: str) -> T | None:
    return find_by_predicate(items, lambda x: x.name == name)
