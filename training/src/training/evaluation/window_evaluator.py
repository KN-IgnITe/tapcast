from dataclasses import dataclass

import pandas as pd

from training.data.columns import PipelineKey
from training.data.mock_data_generator import ArticleKey, DayKey
from training.evaluation.metrics import RegressionMetrics


@dataclass(frozen=True)
class WindowEvaluationResult:
    """Metrics and per-PLU totals for one prediction horizon."""

    window_days: int
    metrics: dict[str, float]
    windows: pd.DataFrame


class WindowEvaluator:
    """Evaluate sums of daily predictions over calendar windows."""

    MIN_WINDOW_DAYS = 1
    MAX_WINDOW_DAYS = 14

    WINDOW_START_COLUMN = "window_start"
    WINDOW_END_COLUMN = "window_end"
    WINDOW_DAYS_COLUMN = "window_days"

    @classmethod
    def evaluate(
        cls,
        predictions: pd.DataFrame,
        window_days: int,
    ) -> WindowEvaluationResult:
        """Aggregate daily predictions and calculate metrics on their sums."""

        windows = cls.aggregate(predictions, window_days)
        target_col = PipelineKey.TARGET_DEMAND.value
        prediction_col = PipelineKey.PREDICTION.value

        metrics = RegressionMetrics.calculate(
            windows[target_col],
            windows[prediction_col],
        )

        return WindowEvaluationResult(
            window_days=window_days,
            metrics=metrics,
            windows=windows,
        )

    @classmethod
    def aggregate(
        cls,
        predictions: pd.DataFrame,
        window_days: int,
    ) -> pd.DataFrame:
        """Build rolling calendar-window totals separately within each fold."""

        cls._validate_window_days(window_days)
        cls._validate_predictions(predictions)

        date_col = DayKey.DATE.value
        fold_col = PipelineKey.BACKTEST_FOLD.value

        data = predictions.copy()
        data[date_col] = pd.to_datetime(data[date_col])

        if fold_col not in data.columns:
            data[fold_col] = 0

        aggregated_windows: list[pd.DataFrame] = []

        for fold_value, fold_df in data.groupby(fold_col, sort=True):
            aggregated_windows.extend(
                cls._aggregate_fold(
                    fold_df=fold_df,
                    fold_value=fold_value,
                    window_days=window_days,
                )
            )

        if not aggregated_windows:
            raise ValueError(
                f"No complete {window_days}-day windows found in predictions."
            )

        return pd.concat(aggregated_windows, ignore_index=True)

    @classmethod
    def _aggregate_fold(
        cls,
        fold_df: pd.DataFrame,
        fold_value: object,
        window_days: int,
    ) -> list[pd.DataFrame]:
        """Build every complete rolling window for one backtest fold."""

        date_col = DayKey.DATE.value
        plu_col = ArticleKey.PLU.value
        category_col = ArticleKey.CATEGORY.value
        target_col = PipelineKey.TARGET_DEMAND.value
        prediction_col = PipelineKey.PREDICTION.value
        fold_col = PipelineKey.BACKTEST_FOLD.value

        unique_dates = pd.Series(fold_df[date_col].unique()).sort_values()
        fold_end = unique_dates.max()
        window_delta = pd.Timedelta(days=window_days - 1)

        fold_windows: list[pd.DataFrame] = []

        for window_start in unique_dates:
            window_end = window_start + window_delta

            if window_end > fold_end:
                continue

            rows_in_window = fold_df[
                fold_df[date_col].between(window_start, window_end)
            ]

            totals = (
                rows_in_window.groupby(
                    [plu_col, category_col],
                    as_index=False,
                    dropna=False,
                )[[target_col, prediction_col]]
                .sum()
                .assign(
                    **{
                        fold_col: fold_value,
                        cls.WINDOW_START_COLUMN: window_start,
                        cls.WINDOW_END_COLUMN: window_end,
                        cls.WINDOW_DAYS_COLUMN: window_days,
                    }
                )
            )

            fold_windows.append(totals)

        return fold_windows

    @classmethod
    def _validate_window_days(cls, window_days: int) -> None:
        if not isinstance(window_days, int) or isinstance(window_days, bool):
            raise TypeError("window_days must be an integer.")

        if not cls.MIN_WINDOW_DAYS <= window_days <= cls.MAX_WINDOW_DAYS:
            raise ValueError(
                "window_days must be between "
                f"{cls.MIN_WINDOW_DAYS} and {cls.MAX_WINDOW_DAYS}."
            )

    @staticmethod
    def _validate_predictions(predictions: pd.DataFrame) -> None:
        required_columns = {
            DayKey.DATE.value,
            ArticleKey.PLU.value,
            ArticleKey.CATEGORY.value,
            PipelineKey.TARGET_DEMAND.value,
            PipelineKey.PREDICTION.value,
        }
        missing_columns = required_columns.difference(predictions.columns)

        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"Missing prediction columns: {missing}")

        if predictions.empty:
            raise ValueError("Predictions cannot be empty.")
