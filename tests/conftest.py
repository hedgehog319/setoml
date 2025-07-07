import pytest

from setoml.settings_source import SettingsSource


@pytest.fixture(scope="function", autouse=True)
def clear_settings() -> None:
    SettingsSource.clear()
