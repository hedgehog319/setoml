import inspect
from types import NoneType
from typing import Any, Type, get_args, get_origin

from setoml.field import Field, UndefinedField


def _flat_annotations(cls: Type[Any]) -> tuple[Any, ...]:
    if not get_origin(cls):
        return (cls,)
    return tuple(annot for arg in get_args(cls) for annot in _flat_annotations(arg))


def _collect_annotations(cls: type) -> dict[str, Any]:
    """
    Collects and merges type hints from cls and its base classes (excluding 'object').
    """
    return {
        k: v
        for base in reversed(inspect.getmro(cls)[:-2])
        for k, v in inspect.get_annotations(base).items()
    }


def get_fields(obj: Any) -> tuple[Field, ...]:
    """
    Retrieves annotated fields of an object or its class,
    preserving MRO order and providing default values.
    """
    cls = obj if isinstance(obj, type) else type(obj)
    return tuple(
        Field(
            name=name,
            default=getattr(obj, name, UndefinedField),
            type=type_,
        )
        for name, type_ in _collect_annotations(cls).items()
        if not name.startswith("__")
    )


def is_optional(field: Field) -> bool:
    """
    Detects Optional types, i.e., Union[..., NoneType].
    """
    return any(annot in (None, NoneType) for annot in _flat_annotations(field.type))


def is_subsetting(value: Any, type_: type) -> bool:
    from setoml import BaseSettings

    return any(issubclass(a, BaseSettings) for a in _flat_annotations(type_)) and (
        value is UndefinedField or isinstance(value, (dict, BaseSettings))
    )
