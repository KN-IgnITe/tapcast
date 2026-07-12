import numpy as np
import pandas as pd
import pytest

from training.data.columns import PipelineKey
from training.data.mock_data_generator import ArticleKey, DayKey
from training.evaluation.window_evaluator import WindowEvaluator


@pytest.fixture
def daily_predictions() -> pd.DataFrame:
    dates = pd.date_range("2026-01-01", periods=14, freq="D").repeat(2)

    return pd.DataFrame(
        {
            DayKey.DATE.value: dates,
            ArticleKey.PLU.value: [101, 102] * 14,
            ArticleKey.CATEGORY.value: [1, 2] * 14,
            PipelineKey.TARGET_DEMAND.value: [1.0, 2.0] * 14,
            PipelineKey.PREDICTION.value: [2.0, 1.0] * 14,
            PipelineKey.BACKTEST_FOLD.value: [1] * 28,
        }
    )


def _single_window_row(
    windows: pd.DataFrame,
    window_start: str,
    plu: int,
) -> pd.Series:
    matching_rows = windows[
        (windows[WindowEvaluator.WINDOW_START_COLUMN] == pd.Timestamp(window_start))
        & (windows[ArticleKey.PLU.value] == plu)
    ]

    assert len(matching_rows) == 1
    return matching_rows.iloc[0]


def test_one_day_window_preserves_daily_values(
    daily_predictions: pd.DataFrame,
) -> None:
    result = WindowEvaluator.evaluate(daily_predictions, window_days=1)
    row = _single_window_row(result.windows, "2026-01-01", 101)

    assert len(result.windows) == 28
    assert row[PipelineKey.TARGET_DEMAND.value] == 1.0
    assert row[PipelineKey.PREDICTION.value] == 2.0
    assert row[WindowEvaluator.WINDOW_END_COLUMN] == pd.Timestamp("2026-01-01")


def test_seven_day_window_sums_each_plu_separately(
    daily_predictions: pd.DataFrame,
) -> None:
    result = WindowEvaluator.evaluate(daily_predictions, window_days=7)
    plu_101 = _single_window_row(result.windows, "2026-01-01", 101)
    plu_102 = _single_window_row(result.windows, "2026-01-01", 102)

    assert len(result.windows) == 16
    assert plu_101[PipelineKey.TARGET_DEMAND.value] == 7.0
    assert plu_101[PipelineKey.PREDICTION.value] == 14.0
    assert plu_102[PipelineKey.TARGET_DEMAND.value] == 14.0
    assert plu_102[PipelineKey.PREDICTION.value] == 7.0


def test_fourteen_day_window_calculates_metrics_on_window_totals(
    daily_predictions: pd.DataFrame,
) -> None:
    result = WindowEvaluator.evaluate(daily_predictions, window_days=14)

    assert len(result.windows) == 2
    assert np.isclose(result.metrics["MAE"], 14.0)
    assert np.isclose(result.metrics["WAPE"], 28.0 / 42.0)


def test_windows_do_not_cross_backtest_fold_boundaries(
    daily_predictions: pd.DataFrame,
) -> None:
    predictions = daily_predictions.copy()
    date_col = DayKey.DATE.value
    fold_col = PipelineKey.BACKTEST_FOLD.value
    predictions[fold_col] = np.where(
        predictions[date_col] < pd.Timestamp("2026-01-08"),
        1,
        2,
    )

    windows = WindowEvaluator.aggregate(predictions, window_days=7)

    assert len(windows) == 4
    assert set(windows[WindowEvaluator.WINDOW_START_COLUMN]) == {
        pd.Timestamp("2026-01-01"),
        pd.Timestamp("2026-01-08"),
    }


@pytest.mark.parametrize("window_days", [0, 15])
def test_window_days_must_be_between_one_and_fourteen(
    daily_predictions: pd.DataFrame,
    window_days: int,
) -> None:
    with pytest.raises(ValueError, match="between 1 and 14"):
        WindowEvaluator.evaluate(daily_predictions, window_days)


def test_window_evaluator_rejects_missing_columns(
    daily_predictions: pd.DataFrame,
) -> None:
    predictions = daily_predictions.drop(columns=[PipelineKey.PREDICTION.value])

    with pytest.raises(ValueError, match="Missing prediction columns: prediction"):
        WindowEvaluator.evaluate(predictions, window_days=7)
