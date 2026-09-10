from unittest.mock import MagicMock

import pandas as pd
import pytest
import training.evaluation.model_comparison as comparison_module
from training.data.data_splitter import DataSplitter
from training.evaluation.backtest import BacktestResult
from training.evaluation.model_backtester import ModelBacktester
from training.evaluation.model_comparison import ModelComparison
from training.features.temporal_matrix_builder import TemporalMatrixBuilder


def test_compare_objectives_runs_each_configured_objective(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_df = pd.DataFrame({"value": [1, 2, 3]})
    splitter = DataSplitter(n_splits=2)
    matrix_builder = TemporalMatrixBuilder()
    metrics = [
        {"MAE": 2.0, "RMSE": 3.0, "R2": 0.7, "WAPE": 0.4},
        {"MAE": 1.5, "RMSE": 2.5, "R2": 0.8, "WAPE": 0.3},
    ]

    results = [
        BacktestResult(
            global_metrics=item,
            fold_metrics=[item],
            per_plu=pd.DataFrame(),
            per_category=pd.DataFrame(),
            predictions=pd.DataFrame({"prediction": [10.0]}),
        )
        for item in metrics
    ]
    backtesters = [MagicMock(spec=ModelBacktester) for _ in results]
    for backtester, result in zip(backtesters, results, strict=True):
        backtester.run.return_value = result

    factory = MagicMock(side_effect=backtesters)
    monkeypatch.setattr(comparison_module, "ModelBacktester", factory)
    comparison = ModelComparison.compare_objectives(raw_df, splitter, matrix_builder)

    assert factory.call_count == len(ModelComparison.objectives)
    assert set(comparison.backtests) == set(ModelComparison.objectives)
    expected_rows = []
    for objective, call, backtester, result in zip(
        ModelComparison.objectives,
        factory.call_args_list,
        backtesters,
        results,
        strict=True,
    ):
        assert call.kwargs["strategy"].objective == objective
        assert call.kwargs["splitter"] is splitter
        assert call.kwargs["matrix_builder"] is matrix_builder
        backtester.run.assert_called_once()
        assert backtester.run.call_args.args[0] is raw_df
        assert comparison.backtests[objective] is result
        expected_rows.append({"objective": objective, **result.global_metrics})
    pd.testing.assert_frame_equal(comparison.summary, pd.DataFrame(expected_rows))


def test_select_best_objective_uses_lowest_metric() -> None:
    comparison = pd.DataFrame(
        [
            {"objective": "count:poisson", "MAE": 2.0, "WAPE": 0.4},
            {"objective": "reg:tweedie", "MAE": 3.0, "WAPE": 0.3},
        ]
    )

    selected = ModelComparison.select_best_objective(comparison, metric="WAPE")

    assert selected == "reg:tweedie"


def test_select_best_objective_uses_mae_as_tie_breaker() -> None:
    comparison = pd.DataFrame(
        [
            {"objective": "count:poisson", "MAE": 2.0, "WAPE": 0.3},
            {"objective": "reg:tweedie", "MAE": 1.5, "WAPE": 0.3},
        ]
    )

    selected = ModelComparison.select_best_objective(comparison, metric="WAPE")

    assert selected == "reg:tweedie"


def test_select_best_objective_rejects_empty_comparison() -> None:
    with pytest.raises(ValueError, match="empty"):
        ModelComparison.select_best_objective(pd.DataFrame())


def test_select_best_objective_rejects_missing_metric() -> None:
    comparison = pd.DataFrame(
        [
            {"objective": "count:poisson", "MAE": 2.0},
            {"objective": "reg:tweedie", "MAE": 1.5},
        ]
    )

    with pytest.raises(ValueError, match="Metric not found"):
        ModelComparison.select_best_objective(comparison, metric="WAPE")
