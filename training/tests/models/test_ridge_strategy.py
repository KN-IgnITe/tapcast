from unittest.mock import MagicMock

import numpy as np
import pandas as pd
from ml_common.model.feature_schema import FeatureSchema
from ml_common.model.model_kind import ModelKind
from ml_common.model.preprocessing import RidgePreprocessor
from sklearn.linear_model import Ridge

from training.models.ridge_strategy import RidgeTrainingStrategy
from training.models.training_strategy import SupervisedDataset


def test_create_preprocessor_uses_selected_schema_and_scaling(
    feature_schema: FeatureSchema,
) -> None:
    strategy = RidgeTrainingStrategy(schema=feature_schema, scale_numeric=False)

    preprocessor = strategy.create_preprocessor()

    assert isinstance(preprocessor, RidgePreprocessor)
    assert preprocessor.schema == feature_schema
    assert preprocessor.scale_numeric is False
    assert strategy.model_kind == ModelKind.RIDGE
    assert strategy.uses_early_stopping is False


def test_fit_trains_model_on_log_transformed_target() -> None:
    train = SupervisedDataset(
        features=pd.DataFrame({"demand_lag_14d": [0.0, 1.0, 2.0, 3.0]}),
        target=pd.Series([1.0, 3.0, 7.0, 15.0]),
    )
    strategy = RidgeTrainingStrategy()
    expected_model = Ridge().fit(train.features, np.log1p(train.target))

    model = strategy.fit(train)

    assert isinstance(model, Ridge)
    np.testing.assert_allclose(
        model.predict(train.features),
        expected_model.predict(train.features),
    )


def test_predict_restores_original_scale_and_clips_negative_values() -> None:
    features = pd.DataFrame({"demand_lag_14d": [5.0, 10.0, 15.0]})
    model = MagicMock(spec=Ridge)
    model.predict.return_value = np.array([-1.0, 0.0, np.log1p(3.0)])
    strategy = RidgeTrainingStrategy()

    predictions = strategy.predict(model, features)

    model.predict.assert_called_once_with(features)
    np.testing.assert_allclose(predictions, [0.0, 0.0, 3.0])
