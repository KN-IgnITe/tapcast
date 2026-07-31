from typing import Dict, List, Protocol

import pandas as pd

from training.data.data_splitter import DataSplitter

from training.data.columns import PipelineKey

from training.evaluation.metrics import RegressionMetrics


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

        target_col: str = PipelineKey.TARGET_DEMAND.value

        for train_idx, val_idx in self.splitter.get_walk_forward_splits(df):
            train_df = df.iloc[train_idx].copy()
            val_df = df.iloc[val_idx].copy()

            y_train = train_df[target_col].astype(float)
            y_val = val_df[target_col].astype(float)

            X_train = train_df.drop(columns=[target_col])
            X_val = val_df.drop(columns=[target_col])

            model.fit(X_train, y_train)
            preds = model.predict(X_val)

            metrics = RegressionMetrics.calculate(y_val, preds)
            fold_metrics.append(metrics)

        return fold_metrics
