import pytest

from setoml.settings import Settings


def test_simple_nested():
    class S2(Settings):
        p1: int  # take value from .toml
        p2: int = 0  # must be overwriten
        p3: int = 0  # have default value
        p4: int | None  # is optional

    class S1(Settings):
        p1: int  # take value from .toml
        p2: int = 0  # must be overwriten
        p3: int = 0  # have default value
        p4: int | None  # is optional

        s2: S2

    class S(Settings):
        p1: int  # take value from .toml
        p2: int = 0  # must be overwriten
        p3: int = 0  # have default value
        p4: int | None  # is optional

        s1: S1

    s = S(setting_files="tests/files/nested.toml").load()
    assert s.p1 == 1
    assert s.p2 == 2
    assert s.s1.p1 == 3
    assert s.s1.p2 == 4
    assert s.s1.s2.p1 == 5
    assert s.s1.s2.p2 == 6


def test_no_require_fields_level1():
    class S1(Settings):
        no_in_toml: int

    class S(Settings):
        s1: S1

    with pytest.raises(Exception):
        S(setting_files="tests/files/nested.toml").load()


def test_no_require_fields_level2():
    class S2(Settings):
        no_in_toml: int

    class S1(Settings):
        s2: S2

    class S(Settings):
        s1: S1

    with pytest.raises(Exception):
        S(setting_files="/tests/files/nested.toml").load()


def test_custom_app_name():
    class S2(Settings):
        p1: int

    class S1(Settings):
        p1: int
        level2: S2 = S2(app_name="s2")

    class S(Settings):
        p1: int
        level1: S1 = S1(app_name="s1")

    s = S(setting_files="tests/files/nested.toml").load()
    assert s.p1 == 1
    assert s.level1.p1 == 3
    assert s.level1.level2.p1 == 5


def test_custom_filenames_in_nested():
    class S2(Settings):
        p1: int

    class S1(Settings):
        p1: int
        s2: S2 = S2(setting_files="tests/files/nested_part2.toml")

    class S(Settings):
        p1: int
        s1: S1

    s = S(setting_files="tests/files/nested.toml").load()
    assert s.p1 == 1
    assert s.s1.p1 == 3
    assert s.s1.s2.p1 == -1
