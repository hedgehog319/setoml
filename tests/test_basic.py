import pytest
from datetime import datetime
from setoml.settings import Settings


def test_attr_filling():
    class S(Settings):
        p1: int = 0  # must be overwriten
        p2: int = 0  # has default value
        p3: int | None  # is optional

    s = S(file_names='tests/files/basic.toml').load()
    assert s.p1 == 1
    assert s.p2 == 0
    assert s.p3 is None


def test_no_require_field():
    class S(Settings):
        p1: int  # fill from .toml
        p2: int | None  # is optional
        p3: int  # must raise exception

    with pytest.raises(Exception):
        S(file_names='tests/files/basic.toml').load()


def test_toml_types():
    class S(Settings):
        p_str: str
        p_int: int
        p_float: float
        p_bool: bool
        p_date: datetime
        p_array: list
        p_table: dict

    # shouldn't raise any error
    S(file_names='tests/files/basic.toml').load()


def test_app_name():
    class S(Settings):
        p: int

    s = S(app_name='custom_app_name', file_names='tests/files/basic.toml')
    assert s.p == 1
