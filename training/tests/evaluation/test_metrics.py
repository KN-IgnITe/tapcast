import numpy as np
import pandas as pd

from training.evaluation.metrics import RegressionMetrics


def test_regression_metrics_returns_expected_values() -> None:
    y_true = pd.Series([10, 20, 30])
    y_pred = pd.Series([12.0, 18.0, 30.0])

    metrics = RegressionMetrics.calculate(y_true, y_pred)

    assert np.isclose(metrics["MAE"], 4 / 3)
    assert np.isclose(metrics["WAPE"], 4 / 60)
    assert "RMSE" in metrics
    assert "R2" in metrics


def test_wape_returns_zero_when_actuals_and_predictions_are_zero() -> None:
    y_true = pd.Series([0, 0, 0])
    y_pred = pd.Series([0, 0, 0])

    assert RegressionMetrics.calculate_wape(y_true, y_pred) == 0.0


def test_wape_returns_inf_when_actuals_are_zero_but_predictions_are_not() -> None:
    y_true = pd.Series([0, 0, 0])
    y_pred = pd.Series([1, 2, 3])

    assert RegressionMetrics.calculate_wape(y_true, y_pred) == float("inf")
