import pandas as pd
import pytest
from ml_common.model.feature_schema import FeatureSchema


@pytest.fixture
def feature_schema() -> FeatureSchema:
    return FeatureSchema(
        name="test-demand",
        version=1,
        columns=("PLU", "category", "avg_temp", "rain"),
        categorical_columns=("PLU", "category"),
    )


@pytest.fixture
def training_features() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "PLU": [101, 102, 101],
            "category": [1, 2, 1],
            "avg_temp": [10.0, 30.0, None],
            "rain": [0.0, 1.0, 2.0],
        },
        index=[10, 20, 30],
    )
