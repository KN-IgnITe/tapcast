import pandas as pd
import pytest

from ml_common.model.feature_schema import FeatureSchema


def test_rejects_categorical_columns_missing_from_schema() -> None:
    with pytest.raises(ValueError, match="Categorical columns are missing"):
        FeatureSchema(
            name="test",
            version=1,
            columns=("PLU", "demand_lag_14d"),
            categorical_columns=("PLU", "category"),
        )


def test_rejects_duplicate_feature_columns() -> None:
    with pytest.raises(ValueError, match="duplicate columns"):
        FeatureSchema(
            name="test",
            version=1,
            columns=("PLU", "PLU"),
            categorical_columns=("PLU",),
        )


def test_select_and_validate_rejects_missing_columns() -> None:
    schema = FeatureSchema(
        name="test",
        version=1,
        columns=("PLU", "category", "rain"),
        categorical_columns=("PLU", "category"),
    )
    features = pd.DataFrame(
        {
            "PLU": [101],
            "category": [1],
        }
    )

    with pytest.raises(ValueError, match="rain"):
        schema.select_and_validate(features)


def test_select_and_validate_orders_columns_and_returns_copy() -> None:
    schema = FeatureSchema(
        name="test",
        version=1,
        columns=("PLU", "category", "rain"),
        categorical_columns=("PLU", "category"),
    )
    features = pd.DataFrame(
        {
            "unused": [99.0],
            "rain": [2.5],
            "category": [1],
            "PLU": [101],
        }
    )

    selected = schema.select_and_validate(features)

    assert list(selected.columns) == ["PLU", "category", "rain"]
    assert "unused" not in selected.columns

    selected.loc[0, "rain"] = 10.0
    assert features.loc[0, "rain"] == 2.5
