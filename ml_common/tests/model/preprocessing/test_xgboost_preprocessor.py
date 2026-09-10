from typing import cast

import pandas as pd
import pytest
from ml_common.model.feature_schema import FeatureSchema
from ml_common.model.preprocessing.xgboost_preprocessor import (
    XGBoostPreprocessor,
)
from pandas import CategoricalDtype


def test_fit_transform_learns_categories_and_preserves_numeric_values(
    feature_schema: FeatureSchema,
    training_features: pd.DataFrame,
) -> None:
    preprocessor = XGBoostPreprocessor(
        schema=feature_schema,
        scale_numeric=False,
    )

    transformed = preprocessor.fit_transform(training_features)

    assert list(transformed.columns) == list(feature_schema.columns)
    assert transformed.index.equals(training_features.index)
    assert isinstance(transformed["PLU"].dtype, CategoricalDtype)
    assert isinstance(transformed["category"].dtype, CategoricalDtype)
    assert list(transformed["PLU"].cat.categories) == [101, 102]
    assert list(transformed["category"].cat.categories) == [1, 2]
    pd.testing.assert_series_equal(
        transformed["avg_temp"],
        training_features["avg_temp"],
    )
    assert transformed["rain"].tolist() == [0.0, 1.0, 2.0]


def test_transform_masks_categories_not_seen_during_fit(
    feature_schema: FeatureSchema,
    training_features: pd.DataFrame,
) -> None:
    preprocessor = XGBoostPreprocessor(schema=feature_schema)
    preprocessor.fit_transform(training_features)
    evaluation_features = pd.DataFrame(
        {
            "PLU": [101, 999],
            "category": [1, 9],
            "avg_temp": [15.0, 25.0],
            "rain": [0.0, 1.0],
        }
    )

    transformed = preprocessor.transform(evaluation_features)

    assert transformed.loc[0, "PLU"] == 101
    assert transformed.loc[0, "category"] == 1
    assert pd.isna(transformed.loc[1, "PLU"])
    assert pd.isna(transformed.loc[1, "category"])


def test_numeric_scaler_is_fitted_only_on_training_features(
    feature_schema: FeatureSchema,
    training_features: pd.DataFrame,
) -> None:
    preprocessor = XGBoostPreprocessor(
        schema=feature_schema,
        scale_numeric=True,
    )

    transformed_train = preprocessor.fit_transform(training_features)
    evaluation_features = pd.DataFrame(
        {
            "PLU": [101],
            "category": [1],
            "avg_temp": [40.0],
            "rain": [3.0],
        }
    )
    transformed_evaluation = preprocessor.transform(evaluation_features)

    assert transformed_train["avg_temp"].mean() == pytest.approx(0.0)
    assert transformed_train["rain"].mean() == pytest.approx(0.0)
    assert cast(float, transformed_evaluation.loc[0, "avg_temp"]) == pytest.approx(2.0)
    assert cast(float, transformed_evaluation.loc[0, "rain"]) > 2.0


def test_transform_rejects_unfitted_preprocessor(
    feature_schema: FeatureSchema,
    training_features: pd.DataFrame,
) -> None:
    preprocessor = XGBoostPreprocessor(schema=feature_schema)

    with pytest.raises(RuntimeError, match="fit_transform"):
        preprocessor.transform(training_features)
