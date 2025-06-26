from collections.abc import Iterable
from pathlib import Path
from typing import Any, TypeAlias


from setoml.compat import toml_load
from setoml.field import UndefinedField
from setoml.utils import (
    get_fields,
    is_optional,
    is_subsettings,
)

FileNamesType: TypeAlias = Iterable[str] | str


class Settings:
    _app_name: str | None

    _file_names: Iterable[Path]
    _secret_names: Iterable[Path]

    _skip_extras: bool

    def __init__(
        self,
        app_name: str | None = None,
        file_names: FileNamesType = "settings.toml",
        secret_names: FileNamesType | None = None,
        skip_extras: bool = True,
        settings_root: str | None = None,
        **kwargs: dict[str, Any],
    ) -> None:
        self._app_name = app_name
        if isinstance(file_names, str):
            file_names = [file_names]

        root = self.get_settings_root(settings_root)
        self._file_names = list(map(lambda x: root / x, file_names))
        self._secret_names = list(map(lambda x: root / x, secret_names or []))
        self._skip_extras = skip_extras

        settings = kwargs.get("_settings_dict", self._load_tomls(self._file_names))
        if self._app_name:
            settings = settings.get(self._app_name, {})

        self.model_validate(settings)

    def get_settings_root(self, root: str | None) -> Path:
        if not root:
            return Path.cwd()

        return Path(root)

    def __init_subclass__(cls) -> None:
        cls._fields = tuple(f.name for f in get_fields(cls))

    def _load_tomls(self, files: Iterable[Path]) -> dict[str, Any]:
        settings = {}
        for file in files:
            settings.update(toml_load(file))
        return settings

    def model_validate(self, settings: dict):
        for field in get_fields(self):
            value = settings.get(field.name, field.default)
            if is_subsettings(value, field.type) and field.default is UndefinedField:
                setattr(
                    self,
                    field.name,
                    field.type(_settings_dict=value),
                )

            else:
                if (
                    not is_optional(field)
                    and field.default is UndefinedField
                    and field.name not in settings
                ):
                    raise Exception(f"Нет ключа {field.name}")
                setattr(self, field.name, value)

    def __repr__(self) -> str:
        text = (
            f"{self.__class__.__qualname__}"
            + "("
            + ", ".join([f"{name}={getattr(self, name)!r}" for name in self._fields])
            + ")"
        )

        return text
