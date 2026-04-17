import json
from pathlib import Path

import pandas as pd
import pytest
from training.data.data_loader import DemandDataLoader
from training.data.mock_data_generator import ArticleKey, DayKey, WeatherKey


@pytest.fixture
def mock_json_data() -> dict:
    return {
        DayKey.DAY_DATA: [
            {
                DayKey.WEATHER: {
                    WeatherKey.AVG_TEMP: 10.7,
                    WeatherKey.TEMP_AMPLITUDE: 5.2,
                    WeatherKey.RAIN: 0.0,
                },
                DayKey.SELLS: {
                    DayKey.ARTICLES: [
                        {
                            ArticleKey.PLU: 123,
                            ArticleKey.CATEGORY: 1,
                            ArticleKey.DEMAND: 25,
                            ArticleKey.YESTERDAY_DEMAND: 20,
                            ArticleKey.WEEK_AGO_DEMAND: 15,
                        },
                        {
                            ArticleKey.PLU: 456,
                            ArticleKey.CATEGORY: 2,
                            ArticleKey.DEMAND: 40,
                            ArticleKey.YESTERDAY_DEMAND: 35,
                            ArticleKey.WEEK_AGO_DEMAND: 30,
                        },
                        {
                            ArticleKey.PLU: 789,
                            ArticleKey.CATEGORY: 3,
                            ArticleKey.DEMAND: 10,
                            ArticleKey.YESTERDAY_DEMAND: 5,
                            ArticleKey.WEEK_AGO_DEMAND: 8,
                        },
                        {
                            ArticleKey.PLU: 101,
                            ArticleKey.CATEGORY: 1,
                            ArticleKey.DEMAND: 15,
                            ArticleKey.YESTERDAY_DEMAND: 10,
                            ArticleKey.WEEK_AGO_DEMAND: 12,
                        },
                    ]
                },
                DayKey.DATE: "2023-01-01",
                DayKey.DAY_OF_WEEK: "3",
                DayKey.IS_WORKING: True,
                DayKey.IS_NEXT_DAY_WORKING: True,
            }
        ]
    }


def test_read_json_raises_error_if_file_missing() -> None:
    """Checks if FileNotFoundError is raised when the JSON file does not exist."""
    loader = DemandDataLoader(
        Path("non_existent_file.json"), Path("non_existent_contract.json")
    )

    with pytest.raises(FileNotFoundError):
        loader._read_json()


def test_flatten_data_raises_error_if_day_data_missing(mock_json_data: dict) -> None:
    """Checks protection against missing 'day_data' key in the JSON structure."""
    loader = DemandDataLoader(Path("dummy_path.json"), Path("dummy_contract.json"))
    bad_data: dict[str, list] = {"some_other_key": []}

    with pytest.raises(ValueError, match="found in the JSON data"):
        loader._flatten_data(bad_data)


def test_flatten_data_creates_correct_flat_structure(mock_json_data: dict) -> None:
    """Checks if json data is correctly ftattened into a DataFrame"""
    loader = DemandDataLoader(Path("dummy_path.json"), Path("dummy_contract.json"))

    df = loader._flatten_data(mock_json_data)

    assert len(df) == 4

    assert df.iloc[0][ArticleKey.PLU] == 123
    assert df.iloc[0][WeatherKey.AVG_TEMP] == 10.7
    assert df.iloc[0][DayKey.IS_WORKING] == 1

    assert df.iloc[3][ArticleKey.PLU] == 101


def test_load_and_process_end_to_end(tmp_path: Path, mock_json_data: dict) -> None:
    """End-to-end test for the entire loading and processing pipeline"""
    json_file = tmp_path / "mock_data.json"

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(mock_json_data, f)

    loader = DemandDataLoader(json_file, Path("dummy_contract.json"))

    df = loader.load_and_process()

    assert len(df) == 4

    assert pd.api.types.is_datetime64_any_dtype(df[DayKey.DATE])
