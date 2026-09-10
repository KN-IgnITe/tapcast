from dataclasses import dataclass
from typing import cast

import pandas as pd

from training.data.data_splitter import DataSplitter
from training.evaluation.backtest import BacktestResult
from training.evaluation.model_backtester import ModelBacktester
from training.features.temporal_matrix_builder import TemporalMatrixBuilder
from training.models.xgboost_strategy import (
    XGBoostObjective,
    XGBoostTrainingStrategy,
)


@dataclass(frozen=True)
class ObjectiveComparisonResult:
    summary: pd.DataFrame
    backtests: dict[XGBoostObjective, BacktestResult]


class ModelComparison:
    """Compare XGBoost objecives using identical temporal splits."""

    objectives: tuple[XGBoostObjective, ...] = (
        "count:poisson",
        "reg:tweedie",
    )

    @classmethod
    def compare_objectives(
        cls,
        df: pd.DataFrame,
        splitter: DataSplitter,
        matrix_builder: TemporalMatrixBuilder,
    ) -> ObjectiveComparisonResult:
        rows: list[dict[str, object]] = []
        backtests: dict[XGBoostObjective, BacktestResult] = {}

        for objective in cls.objectives:
            strategy = XGBoostTrainingStrategy(objective=objective)
            result = ModelBacktester(
                strategy=strategy,
                splitter=splitter,
                matrix_builder=matrix_builder,
            ).run(df)

            backtests[objective] = result
            rows.append({"objective": objective, **result.global_metrics})

        return ObjectiveComparisonResult(
            summary=pd.DataFrame(rows), backtests=backtests
        )

    @staticmethod
    def select_best_objective(
        comparison: pd.DataFrame,
        metric: str = "WAPE",
    ) -> XGBoostObjective:
        """Select objective with the samllest requested error."""

        if comparison.empty:
            raise ValueError("Objective comparison is empty.")

        if metric not in comparison.columns:
            raise ValueError(f"Metric not found: {metric}")

        best_row = comparison.sort_values([metric, "MAE"]).iloc[0]

        return cast(
            XGBoostObjective,
            best_row["objective"],
        )
