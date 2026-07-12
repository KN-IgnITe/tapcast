from types import SimpleNamespace
from typing import Any

import pandas as pd
import pytest

import training.evaluation.model_comparison as model_comparison_module
from training.data.data_splitter import DataSplitter
from training.evaluation.model_comparison import ModelComparison
from training.features.temporal_matrix_builder import TemporalMatrixBuilder
from training.models.model_trainer import ModelType, XGBoostObjective


def test_compare_objectives_runs_each_configured_objective(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_df = pd.DataFrame({"value": [1, 2, 3]})
    splitter = DataSplitter(n_splits=2)
    matrix_builder = TemporalMatrixBuilder()
    called_objectives: list[XGBoostObjective] = []

    class FakeModelTrainer:
        def __init__(
            self,
            model_type: ModelType,
            xgboost_objective: XGBoostObjective,
        ) -> None:
            assert model_type == ModelType.XGBOOST
            self.xgboost_objective = xgboost_objective
            called_objectives.append(xgboost_objective)

        def run_walk_forward_training(
            self,
            df: pd.DataFrame,
            received_splitter: DataSplitter,
            received_matrix_builder: TemporalMatrixBuilder,
        ) -> Any:
            assert df is raw_df
            assert received_splitter is splitter
            assert received_matrix_builder is matrix_builder

            metrics_by_objective = {
                "count:poisson": {
                    "MAE": 2.0,
                    "RMSE": 3.0,
                    "R2": 0.7,
                    "WAPE": 0.4,
                },
                "reg:tweedie": {
                    "MAE": 1.5,
                    "RMSE": 2.5,
                    "R2": 0.8,
                    "WAPE": 0.3,
                },
            }

            return SimpleNamespace(
                global_metrics=metrics_by_objective[self.xgboost_objective]
            )

    monkeypatch.setattr(
        model_comparison_module,
        "ModelTrainer",
        FakeModelTrainer,
    )

    comparison = ModelComparison.compare_objectives(
        raw_df,
        splitter,
        matrix_builder,
    )

    assert called_objectives == list(ModelComparison.objectives)
    assert comparison["objective"].tolist() == list(ModelComparison.objectives)
    assert comparison["WAPE"].tolist() == [0.4, 0.3]


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
