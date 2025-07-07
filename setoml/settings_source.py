import itertools
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Iterable, TypeAlias

from setoml.compat import toml_load
from setoml.exception import SettingsFileNotFoundException

PathLike: TypeAlias = str | Path
PathsLike: TypeAlias = Iterable[Path] | None


class SettingsSource(ABC):
    _cache: dict[str, Any] = {}

    @classmethod
    def load(
        cls,
        setting_files: PathsLike,
        secret_files: PathsLike,
    ) -> dict[str, Any]:
        paths = [f for f in itertools.chain(setting_files or (), secret_files or ())]
        hash = str(paths)

        if hash not in cls._cache:
            for file in paths:
                if not file.exists():
                    raise SettingsFileNotFoundException(
                        f"Settings file not found {file}"
                    )

            cls._cache[hash] = {
                k: v for file in paths for k, v in cls.parse_file(file).items()
            }
        return cls._cache[hash]

    @classmethod
    @abstractmethod
    def parse_file(cls, file_path: Path) -> dict[str, Any]: ...

    @classmethod
    def clear(cls) -> None:
        SettingsSource._cache.clear()


class TOMLSource(SettingsSource):
    @classmethod
    def load(
        cls,
        setting_files: PathsLike,
        secret_files: PathsLike,
    ) -> dict[str, Any]:
        return super().load(
            setting_files=setting_files,
            secret_files=secret_files,
        )

    @classmethod
    def parse_file(cls, file_path: Path) -> dict[str, Any]:
        return toml_load(file_path)
