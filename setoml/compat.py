from pathlib import Path

try:
    import rtoml

    def toml_load(file: Path) -> dict:
        return rtoml.load(file)
except ImportError:
    import tomli

    def toml_load(file: Path) -> dict:
        return tomli.load(open(file, "rb"))
