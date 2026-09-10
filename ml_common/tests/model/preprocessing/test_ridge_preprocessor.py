from typing import cast

import pandas as pd
import pytest
from ml_common.model.feature_schema import FeatureSchema
from ml_common.model.preprocessing.ridge_preprocessor import RidgePreprocessor


def test_fit_transform_imputes_numeric_values_and_encodes_categories(
    feature_schema: FeatureSchema,
    training_features: pd.DataFrame,
) -> None:
    preprocessor = RidgePreprocessor(
        schema=feature_schema,
        scale_numeric=False,
    )

    transformed = preprocessor.fit_transform(training_features)

    assert list(transformed.columns) == [
        "num__avg_temp",
        "num__rain",
        "cat__PLU_101",
        "cat__PLU_102",
        "cat__category_1",
        "cat__category_2",
    ]
    assert transformed.index.equals(training_features.index)
    assert transformed["num__avg_temp"].tolist() == [10.0, 30.0, 20.0]
    assert transformed["cat__PLU_101"].tolist() == [1.0, 0.0, 1.0]
    assert transformed["cat__PLU_102"].tolist() == [0.0, 1.0, 0.0]


def test_transform_ignores_categories_not_seen_during_fit(
    feature_schema: FeatureSchema,
    training_features: pd.DataFrame,
) -> None:
    preprocessor = RidgePreprocessor(
        schema=feature_schema,
        scale_numeric=False,
    )
    transformed_train = preprocessor.fit_transform(training_features)
    evaluation_features = pd.DataFrame(
        {
            "PLU": [999],
            "category": [9],
            "avg_temp": [20.0],
            "rain": [1.0],
        },
        index=[40],
    )

    transformed_evaluation = preprocessor.transform(evaluation_features)
    categorical_columns = [
        column for column in transformed_train.columns if column.startswith("cat__")
    ]

    assert list(transformed_evaluation.columns) == list(transformed_train.columns)
    assert transformed_evaluation.index.equals(evaluation_features.index)
    assert transformed_evaluation.loc[40, categorical_columns].sum() == 0.0


def test_numeric_scaler_is_fitted_only_on_training_features(
    feature_schema: FeatureSchema,
    training_features: pd.DataFrame,
) -> None:
    preprocessor = RidgePreprocessor(
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

    assert transformed_train["num__avg_temp"].mean() == pytest.approx(0.0)
    assert transformed_train["num__rain"].mean() == pytest.approx(0.0)
    assert cast(float, transformed_evaluation.loc[0, "num__avg_temp"]) > 2.0
    assert cast(float, transformed_evaluation.loc[0, "num__rain"]) > 2.0


def test_transform_rejects_unfitted_preprocessor(
    feature_schema: FeatureSchema,
    training_features: pd.DataFrame,
) -> None:
    preprocessor = RidgePreprocessor(schema=feature_schema)

    with pytest.raises(RuntimeError, match="fit_transform"):
        preprocessor.transform(training_features)
