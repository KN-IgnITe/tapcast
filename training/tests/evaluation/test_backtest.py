import numpy as np
import pandas as pd
import pytest
from training.data.columns import PipelineKey
from training.data.data_splitter import DataSplitter
from training.data.mock_data_generator import DayKey
from training.evaluation.backtest import BackTestRunner
from training.evaluation.baseline import Lag14Baseline


@pytest.fixture
def backtest_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            DayKey.DATE.value: pd.date_range("2023-01-01", periods=12),
            PipelineKey.DEMAND_LAG_14D.value: [10] * 12,
            PipelineKey.TARGET_DEMAND.value: [12] * 12,
        }
    )


def test_backtest_runner_returns_metrics_for_each_fold(
    backtest_df: pd.DataFrame,
) -> None:
    df = backtest_df
    splitter = DataSplitter(n_splits=3)
    runner = BackTestRunner(splitter)

    results = runner.run(df, Lag14Baseline())

    assert len(results) == 3

    for metrics in results:
        assert "MAE" in metrics
        assert "WAPE" in metrics
        assert "RMSE" in metrics
        assert "R2" in metrics


def test_backtest_runner_works_with_lag14_baseline(backtest_df: pd.DataFrame) -> None:
    splitter = DataSplitter(n_splits=3)
    runner = BackTestRunner(splitter)

    results = runner.run(backtest_df, Lag14Baseline())

    assert all(np.isclose(metrics["MAE"], 2.0) for metrics in results)


class TrackingModel:
    def __init__(self) -> None:
        self.fit_calls = 0
        self.predict_calls = 0

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series | None = None,
    ) -> "TrackingModel":
        self.fit_calls += 1
        return self

    def predict(self, X: pd.DataFrame) -> pd.Series:
        self.predict_calls += 1
        return pd.Series([10.0] * len(X), index=X.index)


def test_backtest_runner_calls_fit_and_predict_for_each_fold(
    backtest_df: pd.DataFrame,
) -> None:
    splitter = DataSplitter(n_splits=3)
    runner = BackTestRunner(splitter)
    model = TrackingModel()

    runner.run(backtest_df, model)

    assert model.fit_calls == 3
    assert model.predict_calls == 3


class InputCheckingModel:
    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series | None = None,
    ) -> "InputCheckingModel":
        assert y is not None
        assert len(X) == len(y)
        assert PipelineKey.TARGET_DEMAND.value not in X.columns
        return self

    def predict(self, X: pd.DataFrame) -> pd.Series:
        assert PipelineKey.TARGET_DEMAND.value not in X.columns
        return pd.Series([10.0] * len(X), index=X.index)


def test_backtest_runner_does_not_pass_target_as_feature(
    backtest_df: pd.DataFrame,
) -> None:

    splitter = DataSplitter(n_splits=3)
    runner = BackTestRunner(splitter)

    runner.run(backtest_df, InputCheckingModel())
