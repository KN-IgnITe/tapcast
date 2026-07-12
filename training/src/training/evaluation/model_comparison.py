from typing import cast

import pandas as pd

from training.data.data_splitter import DataSplitter
from training.features.temporal_matrix_builder import TemporalMatrixBuilder
from training.models.model_trainer import (
    ModelTrainer,
    ModelType,
    XGBoostObjective,
)


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
    ) -> pd.DataFrame:
        rows: list[dict[str, object]] = []

        for objective in cls.objectives:
            trainer = ModelTrainer(
                model_type=ModelType.XGBOOST, xgboost_objective=objective
            )

            result = trainer.run_walk_forward_training(
                df,
                splitter,
                matrix_builder,
            )

            rows.append({"objective": objective, **result.global_metrics})

        return pd.DataFrame(rows)

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
