from typing import Any

import numpy as np
import pandas as pd
import pytest
from ml_common.model.feature_schema import FeatureSchema
from training.data.mock_data_generator import ArticleKey, DayKey, WeatherKey


def _raw_history_row(
    date: str | pd.Timestamp,
    plu: int,
    category: int,
    demand: int,
    day_of_week: int | None = None,
    is_working: int | None = None,
    is_next_day_working: int | None = None,
) -> dict[str, Any]:
    timestamp = pd.Timestamp(date)

    return {
        DayKey.DATE.value: date,
        DayKey.DAY_OF_WEEK.value: day_of_week or timestamp.isoweekday(),
        DayKey.IS_WORKING.value: (
            int(timestamp.weekday() < 5) if is_working is None else is_working
        ),
        DayKey.IS_NEXT_DAY_WORKING.value: (
            int((timestamp + pd.Timedelta(days=1)).weekday() < 5)
            if is_next_day_working is None
            else is_next_day_working
        ),
        WeatherKey.AVG_TEMP.value: 12.0,
        WeatherKey.TEMP_AMPLITUDE.value: 4.0,
        WeatherKey.RAIN.value: 0.0,
        ArticleKey.PLU.value: plu,
        ArticleKey.CATEGORY.value: category,
        ArticleKey.DEMAND.value: demand,
    }


@pytest.fixture
def raw_history_row_factory() -> Any:
    """Create raw history rows shared by cleaner and temporal builder tests."""

    return _raw_history_row


@pytest.fixture
def feature_schema() -> FeatureSchema:
    return FeatureSchema(
        name="test-demand",
        version=1,
        columns=("PLU", "category", "avg_temp", "demand_lag_14d"),
        categorical_columns=("PLU", "category"),
    )


@pytest.fixture
def dummy_raw_data() -> pd.DataFrame:
    dates = pd.date_range(start="2023-01-01", periods=50).repeat(2)

    return pd.DataFrame(
        {
            DayKey.DATE.value: dates,
            ArticleKey.PLU.value: [101, 102] * 50,
            ArticleKey.CATEGORY.value: [1, 2] * 50,
            ArticleKey.DEMAND.value: [10, 20, 12, 18, 14, 22, 16, 24, 18, 26] * 10,
            DayKey.DAY_OF_WEEK.value: dates.isocalendar().day.to_numpy(),
            DayKey.IS_WORKING.value: (dates.weekday < 5).astype(int),
            DayKey.IS_NEXT_DAY_WORKING.value: (
                (dates + pd.Timedelta(days=1)).weekday < 5
            ).astype(int),
            WeatherKey.AVG_TEMP.value: np.linspace(5.0, 20.0, len(dates)),
            WeatherKey.TEMP_AMPLITUDE.value: np.full(len(dates), 4.0),
            WeatherKey.RAIN.value: np.zeros(len(dates)),
        }
    )
