import pandas as pd

from training.data.columns import PipelineKey


class Lag14Baseline:
    """
    A simple baseline model that uses the value
    from 14 days ago as the prediction.
    """

    def fit(self, X: pd.DataFrame, y: pd.Series | None = None) -> "Lag14Baseline":
        """Dummy fit method to maintain compatibility with scikit-learn API."""
        return self

    def predict(self, X: pd.DataFrame) -> pd.Series:
        """Use demand_lag_14d as baseline prediction"""

        return X[PipelineKey.DEMAND_LAG_14D.value].fillna(0).astype(float)
