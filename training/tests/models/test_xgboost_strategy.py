from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest
from ml_common.model.feature_schema import FeatureSchema
from ml_common.model.model_kind import ModelKind
from ml_common.model.preprocessing import XGBoostPreprocessor
from xgboost import XGBRegressor

from training.models.training_strategy import SupervisedDataset
from training.models.xgboost_strategy import XGBoostObjective, XGBoostTrainingStrategy


@pytest.fixture
def training_data() -> SupervisedDataset:
    return SupervisedDataset(
        features=pd.DataFrame({"demand_lag_14d": [5.0, 10.0, 15.0, 20.0, 25.0, 30.0]}),
        target=pd.Series([6.0, 11.0, 16.0, 21.0, 26.0, 31.0]),
    )


def test_create_preprocessor_uses_selected_schema_and_scaling(
    feature_schema: FeatureSchema,
) -> None:
    strategy = XGBoostTrainingStrategy(schema=feature_schema, scale_numeric=True)

    preprocessor = strategy.create_preprocessor()

    assert isinstance(preprocessor, XGBoostPreprocessor)
    assert preprocessor.schema == feature_schema
    assert preprocessor.scale_numeric is True
    assert strategy.model_kind == ModelKind.XGBOOST


@pytest.mark.parametrize("objective", ["count:poisson", "reg:tweedie"])
def test_fit_uses_selected_configuration_without_early_stopping(
    training_data: SupervisedDataset,
    objective: XGBoostObjective,
) -> None:
    strategy = XGBoostTrainingStrategy(objective=objective, n_estimators=3)

    model = strategy.fit(training_data)

    assert isinstance(model, XGBRegressor)
    assert model.get_params()["objective"] == objective
    assert model.get_params()["n_estimators"] == 3
    assert model.get_params()["early_stopping_rounds"] is None
    predictions = model.predict(training_data.features)
    assert predictions.shape == (len(training_data.target),)
    assert np.isfinite(predictions).all()

    with pytest.raises(RuntimeError, match="not fitted with early stopping"):
        strategy.selected_iteration(model)


def test_early_stopping_returns_selected_tree_count(
    training_data: SupervisedDataset,
) -> None:
    train = SupervisedDataset(
        features=training_data.features.iloc[:4],
        target=training_data.target.iloc[:4],
    )
    validation = SupervisedDataset(
        features=training_data.features.iloc[4:],
        target=training_data.target.iloc[4:],
    )
    strategy = XGBoostTrainingStrategy(n_estimators=20, early_stopping_rounds=2)

    model = strategy.fit_with_early_stopping(train, validation)
    tree_count = strategy.selected_iteration(model)

    assert model.get_params()["early_stopping_rounds"] == 2
    assert tree_count == model.best_iteration + 1
    assert 1 <= tree_count <= strategy.n_estimators


def test_predict_clips_negative_values_to_zero() -> None:
    features = pd.DataFrame({"demand_lag_14d": [5.0, 10.0, 15.0]})
    model = MagicMock(spec=XGBRegressor)
    model.predict.return_value = np.array([-5.0, 0.0, 12.0])
    strategy = XGBoostTrainingStrategy()

    predictions = strategy.predict(model, features)

    model.predict.assert_called_once_with(features)
    np.testing.assert_array_equal(predictions, [0.0, 0.0, 12.0])
