import json
from pathlib import Path
from typing import Any, Dict, List
import jsonschema

import pandas as pd

from training.data.mock_data_generator import ArticleKey, DayKey, WeatherKey


class DemandDataLoader:
    file_path: Path
    contract_path: Path

    def __init__(self, file_path: str | Path, contract_path: str | Path) -> None:
        self.file_path = Path(file_path)
        self.contract_path = Path(contract_path)

    def load_and_process(self) -> pd.DataFrame:
        """load data from JSON and convert to flat DataFrame."""
        raw_data = self._read_json()
        df = self._flatten_data(raw_data)

        df[DayKey.DATE.value] = pd.to_datetime(df[DayKey.DATE.value])

        return df

    def _read_json(self) -> Dict[str, Any]:
        """Load data from JSON file and manage errors if file is missing"""
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")

        """Validate data according to the contract schema"""
        with open(self.file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        with open(self.contract_path, "r", encoding="utf-8") as contract_file:
            contract = json.load(contract_file)
            try:
                jsonschema.validate(
                    instance=data,
                    schema=contract,
                    format_checker=jsonschema.FormatChecker(),
                )
            except jsonschema.ValidationError as e:
                raise ValueError(f"Data validation error: {e}")
        return data

    def _flatten_data(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Flatten the nested JSON structure into a flat DataFrame"""
        flattened_records: List[Dict[str, Any]] = []

        day_data_key = DayKey.DAY_DATA.value
        day_data_list = data.get(day_data_key, data.get(DayKey.DAY_DATA, []))

        if not day_data_list:
            raise ValueError(f"No .{DayKey.DAY_DATA}' found in the JSON data")

        for day in day_data_list:

            base_features = self._extract_day_features(day)

            sells_key = DayKey.SELLS.value
            articles_list: List[Dict[str, int | float]] = day.get(sells_key, [])
            for article in articles_list:
                row = base_features.copy()
                row.update(self._extract_article_features(article))
                flattened_records.append(row)

        return pd.DataFrame(flattened_records)

    def _extract_day_features(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features related to the day (date, day of week, working day)"""

        weather_features = self._extract_weather_features(
            data.get(DayKey.WEATHER.value, {})
        )

        features: Dict[str, Any] = {
            DayKey.DATE.value: str(data.get(DayKey.DATE.value)),
            DayKey.DAY_OF_WEEK.value: int(
                data.get(
                    DayKey.DAY_OF_WEEK.value,
                    pd.Timestamp(data[DayKey.DATE.value]).dayofweek + 1,
                )
            ),
            DayKey.IS_WORKING.value: int(data.get(DayKey.IS_WORKING.value, 0)),
            DayKey.IS_NEXT_DAY_WORKING.value: int(
                data.get(DayKey.IS_NEXT_DAY_WORKING.value, 0)
            ),
        }

        features.update(weather_features)
        return features

    def _extract_weather_features(self, weather: Dict[str, Any]) -> Dict[str, float]:
        return {
            WeatherKey.AVG_TEMP.value: float(
                weather.get(WeatherKey.AVG_TEMP.value, 0.0)
            ),
            WeatherKey.TEMP_AMPLITUDE.value: float(
                weather.get(WeatherKey.TEMP_AMPLITUDE.value, 0.0)
            ),
            WeatherKey.RAIN.value: float(weather.get(WeatherKey.RAIN.value, 0.0)),
        }

    def _extract_article_features(
        self, article: Dict[str, int | float]
    ) -> Dict[str, Any]:
        return {
            ArticleKey.PLU.value: article.get(ArticleKey.PLU.value),
            ArticleKey.CATEGORY.value: article.get(ArticleKey.CATEGORY.value),
            ArticleKey.YESTERDAY_DEMAND.value: article.get(
                ArticleKey.YESTERDAY_DEMAND.value
            ),
            ArticleKey.WEEK_AGO_DEMAND.value: article.get(
                ArticleKey.WEEK_AGO_DEMAND.value
            ),
            ArticleKey.DEMAND.value: article.get(ArticleKey.DEMAND.value),
        }


if __name__ == "__main__":
    data_path = Path(__file__).parents[3] / "data" / "raw" / "test_data.json"
    contract_path = Path(__file__).parent / "contract.json"

    try:
        loader = DemandDataLoader(data_path, contract_path)
        df_flat = loader.load_and_process()

        print(
            f"Data loaded and processed successfully. DataFrame shape: {df_flat.shape}"
        )
        print(df_flat.head())
    except Exception as e:
        print(f"An error occurred during data loading: {e}")
