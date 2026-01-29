from enum import (
    Enum,
    IntEnum,
)
from typing import TypeVar


E = TypeVar('E', bound=Enum)
T = TypeVar('T')
EInt = TypeVar('EInt', bound=IntEnum)
