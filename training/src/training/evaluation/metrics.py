from typing import Dict

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


class RegressionMetrics:
    """Calculates regression metrics used for demand forecasting evaluation."""

    @staticmethod
    def calculate_wape(
        y_true: pd.Series | np.ndarray,
        y_pred: pd.Series | np.ndarray,
    ) -> float:
        """Calculate weighted absolute percentage error."""

        y_true_arr = np.asarray(y_true, dtype=float)
        y_pred_arr = np.asarray(y_pred, dtype=float)

        absolute_error_sum = np.sum(np.abs(y_true_arr - y_pred_arr))
        actual_sum = np.sum(y_true_arr)

        if np.isclose(actual_sum, 0.0):
            if np.isclose(absolute_error_sum, 0.0):
                return 0.0

            return float("nan")

        return float(absolute_error_sum / actual_sum)

    @classmethod
    def calculate(
        cls,
        y_true: pd.Series | np.ndarray,
        y_pred: pd.Series | np.ndarray,
    ) -> Dict[str, float]:
        """Calculate the full set of regression metrics."""

        y_true_arr = np.asarray(y_true, dtype=float)
        y_pred_arr = np.asarray(y_pred, dtype=float)
        r2 = float("nan")

        if y_true_arr.size >= 2:
            r2 = float(r2_score(y_true_arr, y_pred_arr))

        return {
            "MAE": float(mean_absolute_error(y_true_arr, y_pred_arr)),
            "RMSE": float(np.sqrt(mean_squared_error(y_true_arr, y_pred_arr))),
            "R2": r2,
            "WAPE": cls.calculate_wape(y_true_arr, y_pred_arr),
        }

    @classmethod
    def calculate_grouped(
        cls,
        df: pd.DataFrame,
        y_true_col: str,
        y_pred_col: str,
        group_col: str,
    ) -> pd.DataFrame:
        """Calculate metrics for each element in group."""

        rows: list[dict[str, object]] = []

        for group_value in df[group_col].dropna().unique():
            rows.append(
                cls.calculate_for_group_value(
                    df=df,
                    y_true_col=y_true_col,
                    y_pred_col=y_pred_col,
                    group_col=group_col,
                    group_value=group_value,
                )
            )

        return pd.DataFrame(rows)

    @classmethod
    def calculate_for_group_value(
        cls,
        df: pd.DataFrame,
        y_true_col: str,
        y_pred_col: str,
        group_col: str,
        group_value: object,
    ) -> dict[str, object]:
        """Calculate metrics for a specific group value."""

        group_df = df[df[group_col] == group_value]

        if group_df.empty:
            raise ValueError(f"No rows found for group value {group_value}")

        metrics = cls.calculate(
            y_true=group_df[y_true_col],
            y_pred=group_df[y_pred_col],
        )

        return {
            group_col: group_value,
            **metrics,
            "support": len(group_df),
            "actual_sum": float(group_df[y_true_col].sum()),
            "prediction_sum": float(group_df[y_pred_col].sum()),
        }
