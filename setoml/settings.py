from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar
from typing_extensions import Self

from setoml.utils import get_fields, is_optional, is_subsettings, type_validate

from setoml.compat import toml_load


@dataclass(repr=False)
class Settings:
    app_name: str | None = None

    file_names: Iterable[str] | str = "settings.toml"
    secret_names: Iterable[str] | str | None = None

    skip_extras: bool = True
    skip_missing_files: bool = False

    _ignore_fields: ClassVar[set[str]] = field(
        default={
            "app_name",
            "file_names",
            "secret_names",
            "skip_extras",
            "skip_missing_files",
            "_ignore_fields",
        }
    )

    def __post_init__(self) -> None:
        self.settings_root = self.get_settings_root()

        self.load()

    def get_settings_root(self) -> Path:
        return Path.cwd()

    def files_existence(self) -> None:
        if self.skip_missing_files:
            return

        if isinstance(self.file_names, str):
            self.file_names = [self.file_names]
        error_names = [fname for fname in self.file_names if not Path(fname).exists()]

        if error_names:
            raise Exception(
                f"Next files not found: {error_names}"
            )  # REDO: Change message

    def model_validate(self, obj: Any) -> Self:
        for f in get_fields(self):
            if f.name in Settings._ignore_fields:
                continue

            if (
                f.default is None
                and not is_optional(f.type)
                and not obj.get(f.name, None)
            ):
                raise Exception(f"Not set setting {f.name}")

            value = obj.get(f.name, f.default)
            value_type = type(value)

            # REDO:
            if not type_validate(value_type, f.type):
                raise TypeError(
                    f"Field `{f.name}` expected type `{f.type}` but get `{value_type}`"
                )

            if is_subsettings(value_type, f.type):
                if not isinstance(f.default, f.type):
                    value = f.type().model_validate(value)
                else:
                    value = f.default.model_validate(value)

            setattr(self, f.name, value)

        return self

    def load_single(self, filepath: Path) -> dict:
        # TODO: error handling
        settings = toml_load(filepath)
        return settings

    def load(self) -> None:
        self.files_existence()

        settings = {}

        for file in map(Path, self.file_names):
            toml = toml_load(file)
            if self.app_name:
                toml = toml[self.app_name]

            settings.update(toml)

        self.model_validate(settings)

    def __repr__(self) -> str:
        text = (
            f"{self.__class__.__qualname__}"
            + "("
            + ", ".join(
                [
                    f"{f.name}={f.default!r}"
                    for f in get_fields(self)
                    if f.name not in Settings._ignore_fields
                ]
            )
            + ")"
        )

        return text
