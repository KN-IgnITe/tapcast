import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pytest

from training.data.sql_to_json_exporter import (
    DataMapper,
    ExporterPaths,
    SQLToJSONExporter,
)


def test_category_to_int_maps_letters_to_numbers() -> None:
    assert DataMapper.category_to_int("A") == 1
    assert DataMapper.category_to_int("B") == 2
    assert DataMapper.category_to_int("C") == 3
    assert DataMapper.category_to_int("AA") == 27


def test_category_to_int_accepts_numeric_and_empty_values() -> None:
    assert DataMapper.category_to_int(5) == 5
    assert DataMapper.category_to_int("12") == 12
    assert DataMapper.category_to_int(None) == 0
    assert DataMapper.category_to_int("") == 0
    assert DataMapper.category_to_int("   ") == 0


def test_category_to_int_rejects_unsupported_values() -> None:
    with pytest.raises(ValueError, match="Unsupported category value"):
        DataMapper.category_to_int("B-1")


def test_rows_to_contract_groups_rows_and_replaces_nulls() -> None:
    rows = [
        {
            "date": date(2025, 1, 3),
            "day_of_week": 5,
            "is_working": True,
            "is_next_day_working": None,
            "avg_temp": None,
            "temp_amplitude": None,
            "rain": None,
            "plu": 539,
            "category": "B",
            "amount": 20,
            "yesterday_demand": None,
            "week_ago_demand": None,
        },
        {
            "date": date(2025, 1, 3),
            "day_of_week": 5,
            "is_working": True,
            "is_next_day_working": None,
            "avg_temp": None,
            "temp_amplitude": None,
            "rain": None,
            "plu": 542,
            "category": "C",
            "amount": None,
            "yesterday_demand": 7,
            "week_ago_demand": 14,
        },
    ]

    data = DataMapper.rows_to_contract(rows)
    first_day = data["day_data"][0]

    assert len(data["day_data"]) == 1
    assert first_day["date"] == "2025-01-03"
    assert first_day["day_of_week"] == 5
    assert first_day["is_working"] is True
    assert first_day["is_next_day_working"] is False
    assert first_day["weather"] == {
        "avg_temp": 0.0,
        "temp_amplitude": 0.0,
        "rain": 0.0,
    }
    assert first_day["sells"] == [
        {
            "PLU": 539,
            "category": 2,
            "demand": 20,
            "yesterday_demand": 0,
            "week_ago_demand": 0,
        },
        {
            "PLU": 542,
            "category": 3,
            "demand": 0,
            "yesterday_demand": 7,
            "week_ago_demand": 14,
        },
    ]


def test_rows_to_contract_creates_separate_day_entries() -> None:
    rows = [
        {
            "date": date(2025, 1, 3),
            "day_of_week": 5,
            "is_working": True,
            "is_next_day_working": False,
            "avg_temp": 1.5,
            "temp_amplitude": 2.5,
            "rain": 0,
            "plu": 539,
            "category": "B",
            "amount": 20,
            "yesterday_demand": 10,
            "week_ago_demand": 8,
        },
        {
            "date": date(2025, 1, 4),
            "day_of_week": 6,
            "is_working": False,
            "is_next_day_working": False,
            "avg_temp": -1.4,
            "temp_amplitude": 3.6,
            "rain": 1.6,
            "plu": 539,
            "category": "B",
            "amount": 25,
            "yesterday_demand": 20,
            "week_ago_demand": 0,
        },
    ]

    data = DataMapper.rows_to_contract(rows)

    assert [day["date"] for day in data["day_data"]] == [
        "2025-01-03",
        "2025-01-04",
    ]
    assert [len(day["sells"]) for day in data["day_data"]] == [1, 1]


def test_rows_to_contract_accepts_datetime_dates() -> None:
    rows = [
        {
            "date": datetime(2025, 1, 3, 12, 30),
            "day_of_week": 5,
            "is_working": True,
            "is_next_day_working": False,
            "avg_temp": 1.5,
            "temp_amplitude": 2.5,
            "rain": 0,
            "plu": 539,
            "category": "B",
            "amount": 20,
            "yesterday_demand": 10,
            "week_ago_demand": 8,
        }
    ]

    data = DataMapper.rows_to_contract(rows)

    assert data["day_data"][0]["date"] == "2025-01-03"


class FakeDatabaseClient:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.executed_query: str | None = None
        self.executed_params: tuple[int, ...] | None = None

    def fetch(self, query: str, params: tuple[int, ...]) -> list[dict[str, Any]]:
        self.executed_query = query
        self.executed_params = params
        return self.rows


def test_exporter_fetches_rows_validates_and_writes_json(tmp_path: Path) -> None:
    query_path = tmp_path / "query.sql"
    contract_path = tmp_path / "contract.json"
    output_path = tmp_path / "sql_export.json"

    query_path.write_text("SELECT * FROM sale WHERE bar_id = $1", encoding="utf-8")
    contract_path.write_text(
        json.dumps(
            {
                "type": "object",
                "properties": {
                    "day_data": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["date", "weather", "sells"],
                        },
                    }
                },
                "required": ["day_data"],
            }
        ),
        encoding="utf-8",
    )

    rows = [
        {
            "date": date(2025, 1, 3),
            "day_of_week": 5,
            "is_working": True,
            "is_next_day_working": False,
            "avg_temp": 1.5,
            "temp_amplitude": 2.5,
            "rain": 0,
            "plu": 539,
            "category": "B",
            "amount": 20,
            "yesterday_demand": 10,
            "week_ago_demand": 8,
        }
    ]
    client = FakeDatabaseClient(rows)
    paths = ExporterPaths(
        query_path=query_path,
        contract_path=contract_path,
        output_path=output_path,
    )
    exporter = SQLToJSONExporter(client, paths)  # type: ignore[arg-type]

    data = exporter.export(bar_id=1)

    assert client.executed_query == "SELECT * FROM sale WHERE bar_id = $1"
    assert client.executed_params == (1,)
    assert data["day_data"][0]["sells"][0]["demand"] == 20
    assert json.loads(output_path.read_text(encoding="utf-8")) == data
