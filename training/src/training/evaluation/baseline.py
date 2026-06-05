from typing import Dict

import pandas as pd

from training.data.columns import PipelineKey

from training.evaluation.metrics import RegressionMetrics


class Lag14Baseline:
    """
    A simple baseline model that uses the value
    from 14 days ago as the prediction.
    """

    def fit(self, X: pd.DataFrame, y: pd.Series | None = None) -> "Lag14Baseline":
        """Dummy fit method to maintain compatibility with scikit-learn API."""
        return self

    def predict(self, df: pd.DataFrame) -> pd.Series:
        """Use demand_lag_14d as baseline prediction"""

        return df[PipelineKey.DEMAND_LAG_14D.value].fillna(0).astype(float)

    def evaluate(self, df: pd.DataFrame) -> Dict[str, float]:
        """Evaluate lag-14 baseline against target_demand"""

        y_true = df[PipelineKey.TARGET_DEMAND.value].astype(float)
        y_pred = self.predict(df)

        return RegressionMetrics.calculate(y_true, y_pred)
