import json
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Iterable

import jsonschema

from training.data.mock_data_generator import ArticleKey, DayKey, WeatherKey
from training.database.database_client import DatabaseClient
from training.database.database_config import DatabaseConfig


class DBColumn(str, Enum):
    DATE = "date"
    DAY_OF_WEEK = "day_of_week"
    IS_WORKING = "is_working"
    IS_NEXT_DAY_WORKING = "is_next_day_working"
    AVG_TEMP = "avg_temp"
    TEMP_AMPLITUDE = "temp_amplitude"
    RAIN = "rain"
    PLU = "plu"
    CATEGORY = "category"
    AMOUNT = "amount"
    YESTERDAY_DEMAND = "yesterday_demand"
    WEEK_AGO_DEMAND = "week_ago_demand"


@dataclass(frozen=True)
class ExporterPaths:
    query_path: Path
    contract_path: Path
    output_path: Path

    @classmethod
    def resolve_defaults(cls) -> "ExporterPaths":
        current_dir = Path(__file__).resolve()
        project_root = current_dir

        for parent in [current_dir, *current_dir.parents]:
            if (parent / "infrastructure").exists():
                project_root = parent
                break

        return cls(
            query_path=project_root / "infrastructure" / "postgres" / "query.sql",
            contract_path=current_dir.with_name("contract.json"),
            output_path=project_root / "training" / "data" / "raw" / "sql_export.json",
        )


class DataMapper:

    @staticmethod
    def _get_val(row: dict[str, Any], key: DBColumn, default: Any = None) -> Any:
        return row.get(key.value, row.get(key.value.lower(), default))

    @staticmethod
    def _to_int(value: Any) -> int:
        return int(value) if value is not None else 0

    @staticmethod
    def _to_float(value: Any) -> float:
        return float(value) if value is not None else 0.0

    @staticmethod
    def _to_bool(value: Any) -> bool:
        return bool(value) if value is not None else False

    @staticmethod
    def _to_date_string(value: Any) -> str:
        if isinstance(value, datetime):
            return value.date().isoformat()
        if isinstance(value, date):
            return value.isoformat()
        return str(value)

    @staticmethod
    def category_to_int(category: Any) -> int:
        if category is None:
            return 0
        if isinstance(category, int):
            return category

        text = str(category).strip().upper()
        if not text:
            return 0
        if text.isdigit():
            return int(text)
        if not text.isalpha():
            raise ValueError(f"Unsupported category value: {category!r}")

        value = 0
        for char in text:
            value = value * 26 + (ord(char) - ord("A") + 1)
        return value

    @classmethod
    def rows_to_contract(cls, rows: Iterable[dict[str, Any]]) -> dict[str, Any]:

        days_by_date: dict[str, dict[str, Any]] = {}

        for row in rows:
            row_date = cls._to_date_string(cls._get_val(row, DBColumn.DATE))

            if row_date not in days_by_date:
                days_by_date[row_date] = cls._build_day_entry(row, row_date)

            days_by_date[row_date][DayKey.SELLS.value].append(
                cls._build_sell_entry(row)
            )

        return {DayKey.DAY_DATA.value: list(days_by_date.values())}

    @classmethod
    def _build_day_entry(cls, row: dict[str, Any], date_str: str) -> dict[str, Any]:

        return {
            DayKey.DATE.value: date_str,
            DayKey.DAY_OF_WEEK.value: cls._to_int(
                cls._get_val(row, DBColumn.DAY_OF_WEEK)
            ),
            DayKey.IS_WORKING.value: cls._to_bool(
                cls._get_val(row, DBColumn.IS_WORKING)
            ),
            DayKey.IS_NEXT_DAY_WORKING.value: cls._to_bool(
                cls._get_val(row, DBColumn.IS_NEXT_DAY_WORKING)
            ),
            DayKey.WEATHER.value: {
                WeatherKey.AVG_TEMP.value: cls._to_float(
                    cls._get_val(row, DBColumn.AVG_TEMP)
                ),
                WeatherKey.TEMP_AMPLITUDE.value: cls._to_float(
                    cls._get_val(row, DBColumn.TEMP_AMPLITUDE)
                ),
                WeatherKey.RAIN.value: cls._to_float(cls._get_val(row, DBColumn.RAIN)),
            },
            DayKey.SELLS.value: [],
        }

    @classmethod
    def _build_sell_entry(cls, row: dict[str, Any]) -> dict[str, Any]:
        return {
            ArticleKey.PLU.value: cls._to_int(cls._get_val(row, DBColumn.PLU)),
            ArticleKey.CATEGORY.value: cls.category_to_int(
                cls._get_val(row, DBColumn.CATEGORY)
            ),
            ArticleKey.DEMAND.value: cls._to_int(cls._get_val(row, DBColumn.AMOUNT)),
            ArticleKey.YESTERDAY_DEMAND.value: cls._to_int(
                cls._get_val(row, DBColumn.YESTERDAY_DEMAND)
            ),
            ArticleKey.WEEK_AGO_DEMAND.value: cls._to_int(
                cls._get_val(row, DBColumn.WEEK_AGO_DEMAND)
            ),
        }


class SQLToJSONExporter:
    """
    Orchiestrator that fetches data from the database, maps it to the contract format,
    validates it, and writes it to a JSON file.
    """

    def __init__(self, client: DatabaseClient, paths: ExporterPaths) -> None:
        self.client = client
        self.paths = paths

    def export(self, bar_id: int, validate: bool = True) -> dict[str, Any]:
        query = self.paths.query_path.read_text(encoding="utf-8")
        rows = self.client.fetch(query, (bar_id,))

        data = DataMapper.rows_to_contract(rows)

        if validate:
            self._validate_contract(data)

        self._write_json(data)
        return data

    def _validate_contract(self, data: dict[str, Any]) -> None:
        with open(self.paths.contract_path, "r", encoding="utf-8") as f:
            contract = json.load(f)

        jsonschema.validate(
            instance=data,
            schema=contract,
            format_checker=jsonschema.FormatChecker(),
        )

    def _write_json(self, data: dict[str, Any]) -> None:
        self.paths.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.paths.output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def export_from_database(bar_id: int = 1) -> dict[str, Any]:
    config = DatabaseConfig()
    paths = ExporterPaths.resolve_defaults()

    with DatabaseClient(config) as client:
        exporter = SQLToJSONExporter(client, paths)
        return exporter.export(bar_id=bar_id)


if __name__ == "__main__":
    export_from_database()
