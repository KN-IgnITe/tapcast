from typing import Any

import numpy as np
import pandas as pd
import pytest

from training.data.columns import PipelineKey
from training.data.mock_data_generator import ArticleKey, DayKey, WeatherKey
from training.features.history_cleaner import HistoryCleaner


def _history_row(
    date: str,
    plu: int,
    category: int,
    demand: int,
    day_of_week: int = 1,
) -> dict[str, Any]:
    return {
        DayKey.DATE.value: date,
        DayKey.DAY_OF_WEEK.value: day_of_week,
        DayKey.IS_WORKING.value: 1,
        DayKey.IS_NEXT_DAY_WORKING.value: 1,
        WeatherKey.AVG_TEMP.value: 12.0,
        WeatherKey.TEMP_AMPLITUDE.value: 4.0,
        WeatherKey.RAIN.value: 0.0,
        ArticleKey.PLU.value: plu,
        ArticleKey.CATEGORY.value: category,
        ArticleKey.DEMAND.value: demand,
    }


@pytest.fixture
def raw_history_data() -> pd.DataFrame:
    return pd.DataFrame(
        [
            _history_row("2026-01-05", 101, 1, 10, day_of_week=1),
            _history_row("2026-01-12", 101, 1, 20, day_of_week=1),
            _history_row("2026-01-19", 101, 1, 0, day_of_week=1),
            _history_row("2026-01-19", 202, 2, 5, day_of_week=1),
            _history_row("2026-01-06", 104, 1, 4, day_of_week=1),
            _history_row("2026-01-13", 104, 1, 8, day_of_week=1),
            _history_row("2026-01-20", 104, 1, 0, day_of_week=2),
            _history_row("2026-01-20", 202, 2, 5, day_of_week=2),
            _history_row("2026-01-07", 303, 3, 0, day_of_week=1),
            _history_row("2026-01-14", 303, 3, 0, day_of_week=1),
            _history_row("2026-01-21", 303, 3, 5, day_of_week=1),
            _history_row("2026-01-28", 303, 3, 0, day_of_week=1),
            _history_row("2026-01-28", 202, 2, 5, day_of_week=1),
        ]
    )


def _single_cleaned_row(
    df: pd.DataFrame,
    date: str,
    plu: int,
) -> pd.Series:
    matching_rows = df[
        (df[DayKey.DATE.value] == date) & (df[ArticleKey.PLU.value] == plu)
    ]

    assert len(matching_rows) == 1
    return matching_rows.iloc[0]


def test_history_cleaner_creates_expected_output_columns(
    raw_history_data: pd.DataFrame,
) -> None:
    cleaner = HistoryCleaner(winsorized_quantile=1.0)

    cleaned_df = cleaner.clean(raw_history_data)

    expected_columns = [
        DayKey.DATE.value,
        ArticleKey.PLU.value,
        ArticleKey.CATEGORY.value,
        PipelineKey.DEMAND_RAW.value,
        PipelineKey.DEMAND_CLEANED.value,
        PipelineKey.WAS_IMPUTED.value,
        PipelineKey.WAS_WINSORIZED.value,
        PipelineKey.RESTAURANT_TOTAL_DEMAND.value,
        DayKey.DAY_OF_WEEK.value,
        DayKey.IS_WORKING.value,
        DayKey.IS_NEXT_DAY_WORKING.value,
        WeatherKey.AVG_TEMP.value,
        WeatherKey.TEMP_AMPLITUDE.value,
        WeatherKey.RAIN.value,
    ]

    assert list(cleaned_df.columns) == expected_columns
    assert ArticleKey.DEMAND.value not in cleaned_df.columns


def test_history_cleaner_keeps_raw_demand_and_adds_daily_total(
    raw_history_data: pd.DataFrame,
) -> None:
    cleaner = HistoryCleaner(winsorized_quantile=1.0)

    cleaned_df = cleaner.clean(raw_history_data)

    plu_101_zero_day = _single_cleaned_row(cleaned_df, "2026-01-19", 101)
    plu_202_same_day = _single_cleaned_row(cleaned_df, "2026-01-19", 202)

    assert plu_101_zero_day[PipelineKey.DEMAND_RAW.value] == 0
    assert plu_101_zero_day[PipelineKey.RESTAURANT_TOTAL_DEMAND.value] == 5
    assert plu_202_same_day[PipelineKey.RESTAURANT_TOTAL_DEMAND.value] == 5


def test_history_cleaner_imputes_popular_oos_with_day_of_week_median(
    raw_history_data: pd.DataFrame,
) -> None:
    cleaner = HistoryCleaner(winsorized_quantile=1.0)

    cleaned_df = cleaner.clean(raw_history_data)

    imputed_row = _single_cleaned_row(cleaned_df, "2026-01-19", 101)

    assert imputed_row[PipelineKey.DEMAND_CLEANED.value] == 15
    assert imputed_row[PipelineKey.WAS_IMPUTED.value] == 1


def test_history_cleaner_falls_back_to_global_plu_median(
    raw_history_data: pd.DataFrame,
) -> None:
    cleaner = HistoryCleaner(winsorized_quantile=1.0)

    cleaned_df = cleaner.clean(raw_history_data)

    imputed_row = _single_cleaned_row(cleaned_df, "2026-01-20", 104)

    assert imputed_row[PipelineKey.DEMAND_CLEANED.value] == 6
    assert imputed_row[PipelineKey.WAS_IMPUTED.value] == 1


def test_history_cleaner_does_not_impute_rare_product_zero(
    raw_history_data: pd.DataFrame,
) -> None:
    cleaner = HistoryCleaner(winsorized_quantile=1.0)

    cleaned_df = cleaner.clean(raw_history_data)

    rare_product_row = _single_cleaned_row(cleaned_df, "2026-01-28", 303)

    assert rare_product_row[PipelineKey.DEMAND_CLEANED.value] == 0
    assert rare_product_row[PipelineKey.WAS_IMPUTED.value] == 0


def test_history_cleaner_winsorizes_demand_per_plu() -> None:
    raw_df = pd.DataFrame(
        [
            _history_row("2026-02-01", 401, 4, 10),
            _history_row("2026-02-02", 401, 4, 20),
            _history_row("2026-02-03", 401, 4, 100),
        ]
    )

    cleaner = HistoryCleaner(winsorized_quantile=0.5)

    cleaned_df = cleaner.clean(raw_df)
    peak_row = _single_cleaned_row(cleaned_df, "2026-02-03", 401)

    assert peak_row[PipelineKey.DEMAND_CLEANED.value] == 20
    assert peak_row[PipelineKey.WAS_WINSORIZED.value] == 1
    assert np.isclose(cleaner.artifacts_winsorization_threshold[401], 20)
