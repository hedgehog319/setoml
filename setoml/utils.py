import inspect
from dataclasses import dataclass
from types import NoneType
from typing import Any, Type, get_args, get_origin, get_type_hints


@dataclass(frozen=True)
class Field:
    name: str
    default: Any
    type: Any


def _flat_annotations(cls: Type[Any]) -> tuple[Any, ...]:
    if not get_origin(cls):
        return (cls,)
    return tuple(annot for arg in get_args(cls) for annot in _flat_annotations(arg))


def _collect_annotations(cls: Type) -> dict[str, Any]:
    """
    Collects and merges type hints from cls and its base classes (excluding 'object').
    """
    hints: dict[str, Any] = {}
    for base in reversed(inspect.getmro(cls)[:-1]):
        hints.update(get_type_hints(base, include_extras=False))
    return hints


def get_fields(obj: Any) -> tuple[Field, ...]:
    """
    Retrieves annotated fields of an object or its class,
    preserving MRO order and providing default values.
    """
    cls = obj if isinstance(obj, type) else obj.__class__
    return tuple(
        Field(
            name=name,
            default=getattr(obj, name, None),
            type=type_,
        )
        for name, type_ in _collect_annotations(cls).items()
        if not name.startswith("__")
    )


def is_optional(annotation: Any) -> bool:
    """
    Detects Optional types, i.e., Union[..., NoneType].
    """
    flat = _flat_annotations(annotation)
    return any(annot in (None, NoneType) for annot in flat)


def is_subsettings(type_: Type[Any], annotation: Any) -> bool:
    from setoml import Settings  # CHECK: can it be removed from here?

    if type_ is not dict or type_ in (None, NoneType):
        return False

    return any(
        isinstance(arg, type) and issubclass(arg, Settings)
        for arg in _flat_annotations(annotation)
    )


def type_validate(val_type: Type, annotation: Any) -> bool:
    """
    Validates whether 'annotation' allows 'val_type'.
    Supports direct comparison, dict-of-Settings, and Unions.
    """
    from setoml import Settings

    if val_type is annotation:
        return True
    if val_type is dict and issubclass(annotation, Settings):
        return True

    # CHECK: maybe not only Union
    if get_origin(annotation):
        return any(type_validate(val_type, arg) for arg in get_args(annotation))
    return False
