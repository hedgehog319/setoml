import itertools
from pathlib import Path
from typing import Any

from typing_extensions import Self

from setoml.exception import SettingNotExist
from setoml.field import Field, UndefinedField
from setoml.settings_source import PathLike, PathsLike, SettingsSource, TOMLSource
from setoml.utils import (
    get_fields,
    is_optional,
    is_subsetting,
)


class Settings:
    _app_name: str | None
    _setting_files: PathsLike
    _secret_files: PathsLike
    _settings_root: Path

    _settings_source: SettingsSource = TOMLSource()

    def __init__(
        self,
        app_name: str | None = None,
        setting_files: PathsLike | PathLike = None,
        secret_files: PathsLike | PathLike = None,
        settings_root: PathLike = Path.cwd(),
    ) -> None:
        self._app_name = app_name
        self._settings_root = Path(settings_root)

        self._setting_files = self._normalize_path(setting_files)
        self._secret_files = self._normalize_path(secret_files)

    def __init_subclass__(cls, **kwargs) -> None:
        cls._fields = tuple(f.name for f in get_fields(cls))

    def __set_name__(self, _: type, name: str):
        if not self._app_name:
            self._app_name = name

    def _normalize_path(self, files: PathsLike | PathLike) -> tuple[Path, ...] | None:
        if files is None:
            return None
        if isinstance(files, (str, Path)):
            return (self._settings_root / files,)
        return tuple(self._settings_root / f for f in files)

    def load(self, settings: dict[str, Any] | None = None) -> Self:
        has_files = bool(self._setting_files or self._secret_files)
        if settings is None and has_files:
            settings = self._settings_source.load(
                setting_files=self._setting_files,
                secret_files=self._secret_files,
            )

        if settings and self._app_name:
            if self._app_name not in settings:
                setting_files = list(
                    itertools.chain(self._setting_files or (), self._secret_files or ())
                )

                raise SettingNotExist(
                    f"Settings for app `{self._app_name}` not found in files {setting_files}"
                )
            settings = settings[self._app_name]

        if settings and has_files:
            settings |= self._settings_source.load(
                setting_files=self._setting_files,
                secret_files=self._secret_files,
            )

        self.model_validate(settings)

        return self

    def model_validate(self, settings):
        for field in get_fields(self):
            value = settings.get(field.name, field.default)

            if is_subsetting(value, field.type):
                self._init_subsetting(value, field, settings)
            else:
                self._init_required(value, field)

    def _init_subsetting(self, value: Any, field: Field, settings: dict[str, Any]):
        if isinstance(value, Settings):
            setting = value.load(settings)
        elif isinstance(value, dict):
            if isinstance(field.default, Settings):
                setting = field.default.load(settings)
            else:
                setting = field.type().load(value)
                setting._app_name = field.name
        elif value is UndefinedField:
            setting = field.type().load()
        else:
            raise Exception(
                f"Something went wrong in Settings._init_subsetting({value}, {field})"
            )

        setattr(self, field.name, setting)

    def _init_required(self, value: Any, field: Field):
        # CHECK: may be add field.default is UndefinedField
        if value is UndefinedField and not is_optional(field):
            raise Exception(
                f"Setting not found {self.__class__.__qualname__}.{field.name}"
            )
        setattr(self, field.name, value)

    def __repr__(self) -> str:
        params = ", ".join([f"{name}={getattr(self, name)!r}" for name in self._fields])
        return f"{self.__class__.__qualname__}({params})"
