from typing import ClassVar

import numpy as np
import pandas as pd
from ml_common.model.demand_feature_schema import (
    DEMAND_FEATURE_SCHEMA_V1,
)
from ml_common.model.feature_schema import FeatureSchema
from ml_common.model.model_kind import ModelKind
from ml_common.model.preprocessing.ridge_preprocessor import RidgePreprocessor
from sklearn.linear_model import Ridge

from training.models.training_strategy import (
    ModelTrainingStrategy,
    SupervisedDataset,
)


class RidgeTrainingStrategy(ModelTrainingStrategy[Ridge]):
    """Train and use a log-target Ridge demand model."""

    model_kind: ClassVar[ModelKind] = ModelKind.RIDGE

    def __init__(
        self,
        scale_numeric: bool = True,
        schema: FeatureSchema = DEMAND_FEATURE_SCHEMA_V1,
    ) -> None:

        self.scale_numeric = scale_numeric
        self.schema = schema

    @property
    def uses_early_stopping(self) -> bool:
        """Return whether backtesting should use early stopping."""

        return False

    def create_preprocessor(self) -> RidgePreprocessor:
        """Create a fresh Ridge preprocessor."""

        return RidgePreprocessor(
            schema=self.schema,
            scale_numeric=self.scale_numeric,
        )

    def fit(
        self,
        train: SupervisedDataset,
    ) -> Ridge:
        """Create and fit a Ridge regressor on log-transformed demand."""

        model = self._create_model()

        log_target = np.log1p(train.target)

        model.fit(
            train.features,
            log_target,
        )

        return model

    def predict(self, model: Ridge, features: pd.DataFrame) -> np.ndarray:
        """Return non-negative predicitons in the original demand scale."""

        log_predictions = model.predict(features)
        predictions = np.expm1(log_predictions)

        return np.clip(predictions, a_min=0, a_max=None)

    def _create_model(self) -> Ridge:
        """Create an unfitted Ridge regressor."""

        return Ridge()
