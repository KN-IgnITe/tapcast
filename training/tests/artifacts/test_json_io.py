from pathlib import Path

import pytest

from training.artifacts.json_io import JsonExporter, JsonImporter


def test_json_exporter_and_importer_round_trip_dict(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "artifact.json"
    value = {"schema_version": 1, "values": [{"plu": 101, "threshold": 20.5}]}

    JsonExporter().save(value, path)
    loaded = JsonImporter().load(path)

    assert loaded == value


def test_json_importer_raises_when_file_is_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        JsonImporter().load(tmp_path / "missing.json")
