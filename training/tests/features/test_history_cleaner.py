from typing import Any

import numpy as np
import pandas as pd
import pytest

from training.data.columns import PipelineKey
from training.data.mock_data_generator import ArticleKey, DayKey, WeatherKey
from training.features.history_cleaner import HistoryCleaner, HistoryCleanerConfig


@pytest.fixture
def raw_history_data(raw_history_row_factory: Any) -> pd.DataFrame:
    return pd.DataFrame(
        [
            raw_history_row_factory("2026-01-05", 101, 1, 10, day_of_week=1),
            raw_history_row_factory("2026-01-12", 101, 1, 20, day_of_week=1),
            raw_history_row_factory("2026-01-19", 101, 1, 0, day_of_week=1),
            raw_history_row_factory("2026-01-19", 202, 2, 5, day_of_week=1),
            raw_history_row_factory("2026-01-06", 104, 1, 4, day_of_week=1),
            raw_history_row_factory("2026-01-13", 104, 1, 8, day_of_week=1),
            raw_history_row_factory("2026-01-20", 104, 1, 0, day_of_week=2),
            raw_history_row_factory("2026-01-20", 202, 2, 5, day_of_week=2),
            raw_history_row_factory("2026-01-07", 303, 3, 0, day_of_week=1),
            raw_history_row_factory("2026-01-14", 303, 3, 0, day_of_week=1),
            raw_history_row_factory("2026-01-21", 303, 3, 5, day_of_week=1),
            raw_history_row_factory("2026-01-28", 303, 3, 0, day_of_week=1),
            raw_history_row_factory("2026-01-28", 202, 2, 5, day_of_week=1),
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
    cleaner = HistoryCleaner(config=HistoryCleanerConfig(winsorized_quantile=1.0))

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
    cleaner = HistoryCleaner(config=HistoryCleanerConfig(winsorized_quantile=1.0))

    cleaned_df = cleaner.clean(raw_history_data)

    plu_101_zero_day = _single_cleaned_row(cleaned_df, "2026-01-19", 101)
    plu_202_same_day = _single_cleaned_row(cleaned_df, "2026-01-19", 202)

    assert plu_101_zero_day[PipelineKey.DEMAND_RAW.value] == 0
    assert plu_101_zero_day[PipelineKey.RESTAURANT_TOTAL_DEMAND.value] == 5
    assert plu_202_same_day[PipelineKey.RESTAURANT_TOTAL_DEMAND.value] == 5


def test_history_cleaner_keeps_zero_when_oos_imputation_is_disabled(
    raw_history_data: pd.DataFrame,
) -> None:
    cleaner = HistoryCleaner(
        config=HistoryCleanerConfig(
            winsorized_quantile=1.0,
            enable_oos_imputation=False,
        )
    )

    cleaned_df = cleaner.clean(raw_history_data)
    zero_row = _single_cleaned_row(cleaned_df, "2026-01-19", 101)

    assert zero_row[PipelineKey.DEMAND_CLEANED.value] == 0
    assert zero_row[PipelineKey.WAS_IMPUTED.value] == 0
    assert cleaner.artifacts_plu_dow_median == {}
    assert cleaner.artifacts_plu_median == {}
    assert cleaner.artifacts_popular_plu == {}


def test_history_cleaner_imputes_popular_oos_with_day_of_week_median(
    raw_history_data: pd.DataFrame,
) -> None:
    cleaner = HistoryCleaner(
        config=HistoryCleanerConfig(
            winsorized_quantile=1.0,
            enable_oos_imputation=True,
        )
    )
    cleaned_df = cleaner.clean(raw_history_data)

    imputed_row = _single_cleaned_row(cleaned_df, "2026-01-19", 101)

    assert imputed_row[PipelineKey.DEMAND_CLEANED.value] == 15
    assert imputed_row[PipelineKey.WAS_IMPUTED.value] == 1


def test_history_cleaner_falls_back_to_global_plu_median(
    raw_history_data: pd.DataFrame,
) -> None:
    cleaner = HistoryCleaner(
        config=HistoryCleanerConfig(
            winsorized_quantile=1.0,
            enable_oos_imputation=True,
        )
    )

    cleaned_df = cleaner.clean(raw_history_data)

    imputed_row = _single_cleaned_row(cleaned_df, "2026-01-20", 104)

    assert imputed_row[PipelineKey.DEMAND_CLEANED.value] == 6
    assert imputed_row[PipelineKey.WAS_IMPUTED.value] == 1


def test_history_cleaner_does_not_impute_rare_product_zero(
    raw_history_data: pd.DataFrame,
) -> None:
    cleaner = HistoryCleaner(
        config=HistoryCleanerConfig(
            winsorized_quantile=1.0,
            enable_oos_imputation=True,
        )
    )

    cleaned_df = cleaner.clean(raw_history_data)

    rare_product_row = _single_cleaned_row(cleaned_df, "2026-01-28", 303)

    assert rare_product_row[PipelineKey.DEMAND_CLEANED.value] == 0
    assert rare_product_row[PipelineKey.WAS_IMPUTED.value] == 0


def test_history_cleaner_winsorizes_demand_per_plu(
    raw_history_row_factory: Any,
) -> None:
    raw_df = pd.DataFrame(
        [
            raw_history_row_factory("2026-02-01", 401, 4, 10),
            raw_history_row_factory("2026-02-02", 401, 4, 20),
            raw_history_row_factory("2026-02-03", 401, 4, 100),
        ]
    )

    cleaner = HistoryCleaner(
        config=HistoryCleanerConfig(
            winsorized_quantile=0.5,
            min_winsorization_observations=1,
        )
    )

    cleaned_df = cleaner.clean(raw_df)
    peak_row = _single_cleaned_row(cleaned_df, "2026-02-03", 401)

    assert peak_row[PipelineKey.DEMAND_CLEANED.value] == 20
    assert peak_row[PipelineKey.DEMAND_RAW.value] == 100
    assert peak_row[PipelineKey.WAS_WINSORIZED.value] == 1
    assert np.isclose(cleaner.artifacts_winsorization_threshold[401], 20)


def test_history_cleaner_supports_fractional_winsorization_threshold(
    raw_history_row_factory: Any,
) -> None:
    raw_df = pd.DataFrame(
        [
            raw_history_row_factory("2026-02-01", 401, 4, 10),
            raw_history_row_factory("2026-02-02", 401, 4, 20),
            raw_history_row_factory("2026-02-03", 401, 4, 100),
        ]
    )

    cleaned_df = HistoryCleaner(
        config=HistoryCleanerConfig(
            winsorized_quantile=0.95,
            min_winsorization_observations=1,
        )
    ).clean(raw_df)
    peak_row = _single_cleaned_row(cleaned_df, "2026-02-03", 401)

    assert cleaned_df[PipelineKey.DEMAND_CLEANED.value].dtype.kind == "f"
    assert np.isclose(peak_row[PipelineKey.DEMAND_CLEANED.value], 92.0)


def test_history_cleaner_calculates_threshold_from_positive_sales_only(
    raw_history_row_factory: Any,
) -> None:
    raw_df = pd.DataFrame(
        [
            raw_history_row_factory("2026-02-01", 401, 4, 0),
            raw_history_row_factory("2026-02-02", 401, 4, 0),
            raw_history_row_factory("2026-02-03", 401, 4, 10),
            raw_history_row_factory("2026-02-04", 401, 4, 100),
        ]
    )
    cleaner = HistoryCleaner(
        config=HistoryCleanerConfig(
            winsorized_quantile=0.5,
            min_winsorization_observations=2,
        )
    )

    cleaned_df = cleaner.clean(raw_df)
    peak_row = _single_cleaned_row(cleaned_df, "2026-02-04", 401)

    assert np.isclose(cleaner.artifacts_winsorization_threshold[401], 55.0)
    assert np.isclose(peak_row[PipelineKey.DEMAND_CLEANED.value], 55.0)
    assert peak_row[PipelineKey.DEMAND_RAW.value] == 100


def test_history_cleaner_skips_winsorization_below_observation_minimum(
    raw_history_row_factory: Any,
) -> None:
    raw_df = pd.DataFrame(
        [
            raw_history_row_factory("2026-02-01", 401, 4, 10),
            raw_history_row_factory("2026-02-02", 401, 4, 100),
        ]
    )
    cleaner = HistoryCleaner(
        config=HistoryCleanerConfig(
            winsorized_quantile=0.5,
            min_winsorization_observations=3,
        )
    )

    cleaned_df = cleaner.clean(raw_df)
    peak_row = _single_cleaned_row(cleaned_df, "2026-02-02", 401)

    assert 401 not in cleaner.artifacts_winsorization_threshold
    assert peak_row[PipelineKey.DEMAND_CLEANED.value] == 100
    assert peak_row[PipelineKey.WAS_WINSORIZED.value] == 0


def test_history_cleaner_transform_requires_fit(
    raw_history_data: pd.DataFrame,
) -> None:
    cleaner = HistoryCleaner()

    with pytest.raises(RuntimeError, match="Call fit before transform"):
        cleaner.transform(raw_history_data)


def test_history_cleaner_transform_uses_frozen_artifacts(
    raw_history_row_factory: Any,
) -> None:
    train_df = pd.DataFrame(
        [
            raw_history_row_factory("2026-01-05", 101, 1, 10, day_of_week=1),
            raw_history_row_factory("2026-01-12", 101, 1, 20, day_of_week=1),
        ]
    )
    future_df = pd.DataFrame(
        [
            raw_history_row_factory("2026-02-02", 101, 1, 0, day_of_week=1),
            raw_history_row_factory("2026-02-02", 202, 2, 5, day_of_week=1),
            raw_history_row_factory("2026-02-09", 101, 1, 100, day_of_week=1),
        ]
    )

    cleaner = HistoryCleaner(
        config=HistoryCleanerConfig(
            winsorized_quantile=1.0,
            min_winsorization_observations=1,
            enable_oos_imputation=True,
        )
    )
    cleaner.fit(train_df)

    median_artifacts = cleaner.artifacts_plu_median.copy()
    threshold_artifacts = cleaner.artifacts_winsorization_threshold.copy()

    transformed = cleaner.transform(future_df)
    imputed_row = _single_cleaned_row(transformed, "2026-02-02", 101)
    peak_row = _single_cleaned_row(transformed, "2026-02-09", 101)

    assert imputed_row[PipelineKey.DEMAND_CLEANED.value] == 15
    assert imputed_row[PipelineKey.WAS_IMPUTED.value] == 1
    assert peak_row[PipelineKey.DEMAND_CLEANED.value] == 20
    assert peak_row[PipelineKey.WAS_WINSORIZED.value] == 1
    assert cleaner.artifacts_plu_median == median_artifacts
    assert cleaner.artifacts_winsorization_threshold == threshold_artifacts
