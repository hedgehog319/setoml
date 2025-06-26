from collections.abc import Iterable
from pathlib import Path
from typing import Any, TypeAlias
from typing_extensions import Self

from setoml.utils import (
    get_fields,
    is_optional,
    is_subsettings,
    type_validate,
    _flat_annotations,
)

from setoml.compat import toml_load


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
    ) -> None:
        self._app_name = app_name
        if isinstance(file_names, str):
            file_names = [file_names]

        root = self.get_settings_root()
        self._file_names = list(map(lambda x: root / x, file_names))
        self._secret_names = list(map(lambda x: root / x, secret_names or []))
        self._skip_extras = skip_extras

        self.files_existence()

    def __set_name__(self, owner: type[Any], name: str):
        if not issubclass(owner, Settings):
            return

        self._app_name = name

    def __get__(self, instance: Any, owner: type):
        if instance is None:
            return self

        if self._app_name not in instance.__dict__:
            instance.__dict__[self._app_name] = self

        return self

    def get_settings_root(self) -> Path:
        return Path.cwd()

    def files_existence(self) -> None:
        error_settings = [
            fname for fname in self._file_names if not Path(fname).exists()
        ]
        error_secrets = [
            fname for fname in self._secret_names if not Path(fname).exists()
        ]

        message = ""

        if error_settings:
            message += f"Next setting files not found: {error_settings}\n"  # REDO: message text

        if error_secrets:
            message += (
                f"Next secret files not found: {error_secrets}"  # REDO: message text
            )

        if message:
            raise Exception(message)

    def model_validate(self, obj: Any) -> Self:
        if not obj:
            for f in get_fields(self):
                if f.default is None and not is_optional(f.type):
                    raise Exception(f"Not set setting {f.name}")

            return self

        for f in get_fields(self):
            value = obj.get(f.name, f.default)
            value_type = type(value)

            _is_subsettings = is_subsettings(value_type, f.type) or (
                value is None and Settings in _flat_annotations(f.type)
            )

            if (
                f.default is None
                and not is_optional(f.type)
                and f.name not in obj
                and not _is_subsettings
            ):
                raise Exception(f"Not set setting {f.name}")

            # REDO:
            if not (type_validate(value_type, f.type) or _is_subsettings):
                raise TypeError(
                    f"Field `{f.name}` expected type `{f.type}` but get `{value_type}`"
                )

            if _is_subsettings:
                if not isinstance(f.default, f.type):
                    value = f.type(app_name=f.name).model_validate(value)
                else:
                    value = f.default.model_validate(value)

            setattr(self, f.name, value)

        return self

    def load_single(self, filepath: Path) -> dict:
        # TODO: error handling
        settings = toml_load(filepath)
        return settings

    def load(self) -> Self:
        self.files_existence()

        settings = {}

        for file in map(Path, self._file_names):
            toml = toml_load(file)
            if self._app_name:
                toml = toml[self._app_name]

            settings.update(toml)

        return self.model_validate(settings)

    def __repr__(self) -> str:
        text = (
            f"{self.__class__.__qualname__}"
            + "("
            + ", ".join([f"{f.name}={f.default!r}" for f in get_fields(self)])
            + ")"
        )

        return text
