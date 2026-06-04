from typing import Any

import numpy as np
import pandas as pd
import pytest

from training.data.columns import PipelineKey
from training.data.mock_data_generator import ArticleKey, DayKey, WeatherKey
from training.features.training_matrix_builder import TrainingMatrixBuilder


def _cleaned_history_row(
    date: pd.Timestamp,
    plu: int,
    category: int,
    demand: int,
    restaurant_total: int,
    was_imputed: int = 0,
    was_winsorized: int = 0,
) -> dict[str, Any]:
    return {
        DayKey.DATE.value: date.strftime("%Y-%m-%d"),
        ArticleKey.PLU.value: plu,
        ArticleKey.CATEGORY.value: category,
        PipelineKey.DEMAND_RAW.value: demand,
        PipelineKey.DEMAND_CLEANED.value: demand,
        PipelineKey.WAS_IMPUTED.value: was_imputed,
        PipelineKey.WAS_WINSORIZED.value: was_winsorized,
        PipelineKey.RESTAURANT_TOTAL_DEMAND.value: restaurant_total,
        DayKey.DAY_OF_WEEK.value: date.isoweekday(),
        DayKey.IS_WORKING.value: int(date.weekday() < 5),
        DayKey.IS_NEXT_DAY_WORKING.value: int(
            (date + pd.Timedelta(days=1)).weekday() < 5
        ),
        WeatherKey.AVG_TEMP.value: 10.0 + date.day,
        WeatherKey.TEMP_AMPLITUDE.value: 4.0,
        WeatherKey.RAIN.value: 0.0,
    }


@pytest.fixture
def cleaned_history_data() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    for day_number, date in enumerate(
        pd.date_range("2026-01-01", periods=30, freq="D"),
        start=1,
    ):
        plu_101_demand = day_number
        plu_102_demand = day_number * 2
        plu_201_demand = day_number + 10
        restaurant_total = plu_101_demand + plu_102_demand + plu_201_demand

        rows.append(
            _cleaned_history_row(
                date=date,
                plu=101,
                category=1,
                demand=plu_101_demand,
                restaurant_total=restaurant_total,
                was_imputed=int(day_number == 8),
                was_winsorized=int(day_number == 1),
            )
        )
        rows.append(
            _cleaned_history_row(
                date=date,
                plu=102,
                category=1,
                demand=plu_102_demand,
                restaurant_total=restaurant_total,
                was_winsorized=int(day_number == 7),
            )
        )
        rows.append(
            _cleaned_history_row(
                date=date,
                plu=201,
                category=2,
                demand=plu_201_demand,
                restaurant_total=restaurant_total,
            )
        )

    return pd.DataFrame(rows)


def _single_matrix_row(
    df: pd.DataFrame,
    date: str,
    plu: int,
) -> pd.Series:
    matching_rows = df[
        (df[DayKey.DATE.value] == pd.Timestamp(date))
        & (df[ArticleKey.PLU.value] == plu)
    ]

    assert len(matching_rows) == 1
    return matching_rows.iloc[0]


def test_training_matrix_builder_creates_expected_output_columns(
    cleaned_history_data: pd.DataFrame,
) -> None:
    builder = TrainingMatrixBuilder()

    matrix = builder.build(cleaned_history_data)

    expected_columns = [
        DayKey.DATE.value,
        ArticleKey.PLU.value,
        ArticleKey.CATEGORY.value,
        WeatherKey.AVG_TEMP.value,
        WeatherKey.TEMP_AMPLITUDE.value,
        WeatherKey.RAIN.value,
        DayKey.DAY_OF_WEEK.value,
        PipelineKey.DAY_OF_MONTH.value,
        DayKey.IS_WORKING.value,
        DayKey.IS_NEXT_DAY_WORKING.value,
        PipelineKey.DEMAND_LAG_14D.value,
        PipelineKey.DEMAND_LAG_14D_WAS_IMPUTED.value,
        PipelineKey.DEMAND_LAG_14D_WAS_WINSORIZED.value,
        PipelineKey.DEMAND_LAG_21D.value,
        PipelineKey.DEMAND_LAG_21D_WAS_IMPUTED.value,
        PipelineKey.DEMAND_LAG_21D_WAS_WINSORIZED.value,
        PipelineKey.RESTAURANT_TOTAL_DEMAND_LAG_14D.value,
        PipelineKey.DEMAND_LAST_SIMILAR_DAY.value,
        PipelineKey.DEMAND_LAST_SIMILAR_DAY_WAS_IMPUTED.value,
        PipelineKey.DEMAND_LAST_SIMILAR_DAY_WAS_WINSORIZED.value,
        PipelineKey.PLU_ROLLING_MEDIAN_7D.value,
        PipelineKey.PLU_ROLLING_MEDIAN_7D_IMPUTED_COUNT.value,
        PipelineKey.PLU_ROLLING_MEDIAN_7D_WINSORIZED_COUNT.value,
        PipelineKey.CATEGORY_ROLLING_MEDIAN_7D.value,
        PipelineKey.CATEGORY_ROLLING_MEDIAN_7D_IMPUTED_COUNT.value,
        PipelineKey.CATEGORY_ROLLING_MEDIAN_7D_WINSORIZED_COUNT.value,
        PipelineKey.TARGET_DEMAND.value,
    ]

    assert list(matrix.columns) == expected_columns
    assert PipelineKey.DEMAND_RAW.value not in matrix.columns
    assert PipelineKey.DEMAND_CLEANED.value not in matrix.columns


def test_training_matrix_builder_maps_target_context(
    cleaned_history_data: pd.DataFrame,
) -> None:
    builder = TrainingMatrixBuilder()

    matrix = builder.build(cleaned_history_data)
    row = _single_matrix_row(matrix, "2026-01-22", 101)

    assert row[PipelineKey.DAY_OF_MONTH.value] == 22
    assert row[PipelineKey.TARGET_DEMAND.value] == 22
    assert row[WeatherKey.AVG_TEMP.value] == 32.0


def test_training_matrix_builder_adds_exact_lags_and_quality_flags(
    cleaned_history_data: pd.DataFrame,
) -> None:
    builder = TrainingMatrixBuilder()

    matrix = builder.build(cleaned_history_data)
    row = _single_matrix_row(matrix, "2026-01-22", 101)

    assert row[PipelineKey.DEMAND_LAG_14D.value] == 8
    assert row[PipelineKey.DEMAND_LAG_14D_WAS_IMPUTED.value] == 1
    assert row[PipelineKey.DEMAND_LAG_14D_WAS_WINSORIZED.value] == 0
    assert row[PipelineKey.DEMAND_LAG_21D.value] == 1
    assert row[PipelineKey.DEMAND_LAG_21D_WAS_IMPUTED.value] == 0
    assert row[PipelineKey.DEMAND_LAG_21D_WAS_WINSORIZED.value] == 1


def test_training_matrix_builder_fills_missing_lag_flags_with_zero(
    cleaned_history_data: pd.DataFrame,
) -> None:
    builder = TrainingMatrixBuilder()

    matrix = builder.build(cleaned_history_data)
    row = _single_matrix_row(matrix, "2026-01-01", 101)

    assert np.isnan(row[PipelineKey.DEMAND_LAG_14D.value])
    assert row[PipelineKey.DEMAND_LAG_14D_WAS_IMPUTED.value] == 0
    assert row[PipelineKey.DEMAND_LAG_14D_WAS_WINSORIZED.value] == 0


def test_training_matrix_builder_adds_restaurant_total_demand_lag(
    cleaned_history_data: pd.DataFrame,
) -> None:
    builder = TrainingMatrixBuilder()

    matrix = builder.build(cleaned_history_data)
    row = _single_matrix_row(matrix, "2026-01-22", 101)

    assert row[PipelineKey.RESTAURANT_TOTAL_DEMAND_LAG_14D.value] == 42


def test_training_matrix_builder_adds_smart_lag_with_quality_flags(
    cleaned_history_data: pd.DataFrame,
) -> None:
    builder = TrainingMatrixBuilder()

    matrix = builder.build(cleaned_history_data)
    row = _single_matrix_row(matrix, "2026-01-22", 101)

    assert row[PipelineKey.DEMAND_LAST_SIMILAR_DAY.value] == 8
    assert row[PipelineKey.DEMAND_LAST_SIMILAR_DAY_WAS_IMPUTED.value] == 1
    assert row[PipelineKey.DEMAND_LAST_SIMILAR_DAY_WAS_WINSORIZED.value] == 0


def test_training_matrix_builder_adds_plu_rolling_median_and_quality_counts(
    cleaned_history_data: pd.DataFrame,
) -> None:
    builder = TrainingMatrixBuilder()

    matrix = builder.build(cleaned_history_data)
    row = _single_matrix_row(matrix, "2026-01-22", 101)

    assert row[PipelineKey.PLU_ROLLING_MEDIAN_7D.value] == 5
    assert row[PipelineKey.PLU_ROLLING_MEDIAN_7D_IMPUTED_COUNT.value] == 1
    assert row[PipelineKey.PLU_ROLLING_MEDIAN_7D_WINSORIZED_COUNT.value] == 0


def test_training_matrix_builder_adds_category_rolling_median_and_quality_counts(
    cleaned_history_data: pd.DataFrame,
) -> None:
    builder = TrainingMatrixBuilder()

    matrix = builder.build(cleaned_history_data)
    row = _single_matrix_row(matrix, "2026-01-22", 101)

    assert row[PipelineKey.CATEGORY_ROLLING_MEDIAN_7D.value] == 15
    assert row[PipelineKey.CATEGORY_ROLLING_MEDIAN_7D_IMPUTED_COUNT.value] == 1
    assert row[PipelineKey.CATEGORY_ROLLING_MEDIAN_7D_WINSORIZED_COUNT.value] == 1


def test_training_matrix_builder_smart_lag_skips_missing_days(
    cleaned_history_data: pd.DataFrame,
) -> None:
    broken_history = cleaned_history_data[
        cleaned_history_data[DayKey.DATE.value] != "2026-01-08"
    ]

    builder = TrainingMatrixBuilder()
    matrix = builder.build(broken_history)
    row = _single_matrix_row(matrix, "2026-01-22", 101)

    assert row[PipelineKey.DEMAND_LAST_SIMILAR_DAY.value] != 8

    assert not np.isnan(row[PipelineKey.DEMAND_LAST_SIMILAR_DAY_WAS_IMPUTED.value])


def test_training_matrix_builder_smart_lag_respects_max_backwards_limit(
    cleaned_history_data: pd.DataFrame,
) -> None:
    builder = TrainingMatrixBuilder()
    date_col = DayKey.DATE.value
    plu_col = ArticleKey.PLU.value

    broken_history = cleaned_history_data[
        ~cleaned_history_data[date_col].isin(["2026-01-08", "2026-01-07"])
    ]

    df_hist = builder._prepare_history(broken_history)
    df_target = df_hist[
        (df_hist[date_col] == pd.Timestamp("2026-01-22")) & (df_hist[plu_col] == 101)
    ].copy()

    limited_matrix = builder._add_smart_lag(
        df_target=df_target,
        df_hist=df_hist,
        max_backwards_limit=1,
    )
    limited_row = limited_matrix.iloc[0]

    assert np.isnan(limited_row[PipelineKey.DEMAND_LAST_SIMILAR_DAY.value])
    assert limited_row[PipelineKey.DEMAND_LAST_SIMILAR_DAY_WAS_IMPUTED.value] == 0
    assert limited_row[PipelineKey.DEMAND_LAST_SIMILAR_DAY_WAS_WINSORIZED.value] == 0

    wider_matrix = builder._add_smart_lag(
        df_target=df_target,
        df_hist=df_hist,
        max_backwards_limit=2,
    )
    wider_row = wider_matrix.iloc[0]

    assert wider_row[PipelineKey.DEMAND_LAST_SIMILAR_DAY.value] == 6
