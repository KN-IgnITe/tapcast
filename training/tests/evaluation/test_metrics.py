import numpy as np
import pandas as pd

import pytest
from training.evaluation.metrics import RegressionMetrics
from training.data.columns import PipelineKey
from training.data.mock_data_generator import ArticleKey


@pytest.fixture
def metrics_group_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            ArticleKey.PLU.value: [101, 101, 102, 102],
            ArticleKey.CATEGORY.value: [1, 1, 2, 2],
            PipelineKey.TARGET_DEMAND.value: [10, 20, 5, 15],
            "prediction": [12, 18, 4, 16],
        }
    )


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


def test_calculate_for_group_value_returns_metrics_for_single_plu(
    metrics_group_df: pd.DataFrame,
) -> None:
    result = RegressionMetrics.calculate_for_group_value(
        metrics_group_df,
        y_true_col=PipelineKey.TARGET_DEMAND.value,
        y_pred_col="prediction",
        group_col=ArticleKey.PLU.value,
        group_value=101,
    )

    assert result[ArticleKey.PLU.value] == 101
    assert result["support"] == 2
    assert result["actual_sum"] == 30
    assert result["prediction_sum"] == 30
    assert np.isclose(result["MAE"], 2.0)
    assert np.isclose(result["WAPE"], 4 / 30)


def test_calculate_for_group_value_for_returns_metrics_for_single_category(
    metrics_group_df: pd.DataFrame,
) -> None:
    result = RegressionMetrics.calculate_for_group_value(
        df=metrics_group_df,
        y_true_col=PipelineKey.TARGET_DEMAND.value,
        y_pred_col="prediction",
        group_col=ArticleKey.CATEGORY.value,
        group_value=2,
    )

    assert result[ArticleKey.CATEGORY.value] == 2
    assert result["support"] == 2
    assert result["actual_sum"] == 20
    assert result["prediction_sum"] == 20
    assert np.isclose(result["MAE"], 1.0)
    assert np.isclose(result["WAPE"], 2 / 20)


def test_calculate_grouped_returns_one_row_per_plu(
    metrics_group_df: pd.DataFrame,
) -> None:
    result = RegressionMetrics.calculate_grouped(
        df=metrics_group_df,
        y_true_col=PipelineKey.TARGET_DEMAND.value,
        y_pred_col="prediction",
        group_col=ArticleKey.PLU.value,
    )

    assert set(result[ArticleKey.PLU.value]) == {101, 102}
    assert len(result) == 2
    assert set(result["support"]) == {2}


def test_calculate_grouped_returns_metrics_per_category(
    metrics_group_df: pd.DataFrame,
) -> None:
    result = RegressionMetrics.calculate_grouped(
        df=metrics_group_df,
        y_true_col=PipelineKey.TARGET_DEMAND.value,
        y_pred_col="prediction",
        group_col=ArticleKey.CATEGORY.value,
    )

    assert set(result[ArticleKey.CATEGORY.value]) == {1, 2}
    assert len(result) == 2
    assert "MAE" in result.columns
    assert "WAPE" in result.columns
    assert "actual_sum" in result.columns
    assert "prediction_sum" in result.columns


def test_calculate_for_group_value_raises_error_for_missing_group(
    metrics_group_df: pd.DataFrame,
) -> None:
    with pytest.raises(ValueError, match="No rows found for group value 999"):
        RegressionMetrics.calculate_for_group_value(
            df=metrics_group_df,
            y_true_col=PipelineKey.TARGET_DEMAND.value,
            y_pred_col="prediction",
            group_col=ArticleKey.PLU.value,
            group_value=999,
        )
