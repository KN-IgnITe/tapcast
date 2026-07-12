from dataclasses import dataclass
from typing import Dict, List, Protocol

import pandas as pd

from training.data.data_splitter import DataSplitter

from training.data.columns import PipelineKey

from training.evaluation.metrics import RegressionMetrics
from training.features.temporal_matrix_builder import TemporalMatrixBuilder


@dataclass
class BacktestResult:
    global_metrics: dict[str, float]
    fold_metrics: list[dict[str, float]]
    per_plu: pd.DataFrame
    per_category: pd.DataFrame
    predictions: pd.DataFrame


class BackTestModel(Protocol):
    """Model-like interface for BackTestRunner."""

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series | None = None,
    ) -> "BackTestModel": ...

    def predict(self, X: pd.DataFrame) -> pd.Series: ...


class BackTestRunner:
    """Runs chronological walk-forward backtesting."""

    splitter: DataSplitter

    def __init__(self, splitter: DataSplitter) -> None:
        self.splitter = splitter

    def run(
        self,
        df: pd.DataFrame,
        model: BackTestModel,
    ) -> List[Dict[str, float]]:
        """Evaluate model on walk-forward validation splits."""

        fold_metrics: List[Dict[str, float]] = []

        for train_idx, val_idx in self.splitter.get_walk_forward_splits(df):
            train_df = df.iloc[train_idx].copy()
            val_df = df.iloc[val_idx].copy()

            fold_metrics.append(
                self._evaluate_matrices(
                    train_df,
                    val_df,
                    model,
                )
            )

        return fold_metrics

    def run_raw(
        self,
        raw_df: pd.DataFrame,
        model: BackTestModel,
        matrix_builder: TemporalMatrixBuilder,
    ) -> List[Dict[str, float]]:
        """Evaluate model with fold-specific cleaning and features."""

        fold_metrics: List[Dict[str, float]] = []

        for train_idx, val_idx in self.splitter.get_walk_forward_splits(raw_df):
            raw_train = raw_df.iloc[train_idx].copy()
            raw_val = raw_df.iloc[val_idx].copy()
            train_matrix, val_matrix = matrix_builder.build_train_evaluation(
                raw_train,
                raw_val,
            )

            fold_metrics.append(
                self._evaluate_matrices(
                    train_matrix,
                    val_matrix,
                    model,
                )
            )

        return fold_metrics

    def _evaluate_matrices(
        self,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
        model: BackTestModel,
    ) -> Dict[str, float]:
        """Fit and evaluate one pair of prepared matrices."""

        target_col = PipelineKey.TARGET_DEMAND.value
        y_train = train_df[target_col].astype(float)
        y_val = val_df[target_col].astype(float)

        X_train = train_df.drop(columns=[target_col])
        X_val = val_df.drop(columns=[target_col])

        model.fit(X_train, y_train)
        preds = model.predict(X_val)

        return RegressionMetrics.calculate(y_val, preds)
