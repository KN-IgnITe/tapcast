from typing import Any

import pandas as pd
import pytest

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
