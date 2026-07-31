import numpy as np
import pandas as pd

from training.data.columns import PipelineKey
from training.evaluation.baseline import Lag14Baseline


def test_lag14_baseline_predicts_demand_lag_14d() -> None:
    df = pd.DataFrame(
        {
            PipelineKey.DEMAND_LAG_14D.value: [10, 20, 30],
            PipelineKey.TARGET_DEMAND.value: [12, 18, 33],
        }
    )

    baseline = Lag14Baseline()

    preds = baseline.predict(df)

    assert preds.tolist() == [10.0, 20.0, 30.0]


def test_lag14_baseline_fills_missing_lag_with_zero() -> None:
    df = pd.DataFrame(
        {
            PipelineKey.DEMAND_LAG_14D.value: [10, np.nan, 30],
            PipelineKey.TARGET_DEMAND.value: [12, 18, 33],
        }
    )

    baseline = Lag14Baseline()

    preds = baseline.predict(df)

    assert preds.tolist() == [10.0, 0.0, 30.0]


def test_lag14_baseline_fit_returns_self() -> None:
    df = pd.DataFrame(
        {
            PipelineKey.DEMAND_LAG_14D.value: [10, 20],
        }
    )

    baseline = Lag14Baseline()

    fitted = baseline.fit(df)

    assert fitted is baseline
