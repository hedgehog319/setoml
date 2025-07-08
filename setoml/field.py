from dataclasses import dataclass
from typing import Any


class _UndefinedField:
    __slots__: tuple = ()

    def __bool__(self):
        return False

    def __repr__(self):
        return "UndefinedField"


UndefinedField = _UndefinedField()


@dataclass(frozen=True, slots=True, repr=True)
class Field:
    name: str
    default: Any
    type: Any
