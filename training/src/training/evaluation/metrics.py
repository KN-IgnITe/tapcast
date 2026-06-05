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

            return float("inf")

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

        return {
            "MAE": float(mean_absolute_error(y_true_arr, y_pred_arr)),
            "RMSE": float(np.sqrt(mean_squared_error(y_true_arr, y_pred_arr))),
            "R2": float(r2_score(y_true_arr, y_pred_arr)),
            "WAPE": cls.calculate_wape(y_true_arr, y_pred_arr),
        }
