from typing import ClassVar, Literal

import numpy as np
import pandas as pd
from ml_common.model.demand_feature_schema import (
    DEMAND_FEATURE_SCHEMA_V1,
)
from ml_common.model.feature_schema import FeatureSchema
from ml_common.model.model_kind import ModelKind
from ml_common.model.preprocessing import XGBoostPreprocessor
from xgboost import XGBRegressor

from training.models.early_stopping_strategy import (
    EarlyStoppingTrainingStrategy,
)
from training.models.training_strategy import (
    SupervisedDataset,
)

XGBoostObjective = Literal[
    "count:poisson",
    "reg:tweedie",
]


class XGBoostTrainingStrategy(EarlyStoppingTrainingStrategy[XGBRegressor]):
    """Train and use an XGBoost demand model."""

    model_kind: ClassVar[ModelKind] = ModelKind.XGBOOST

    def __init__(
        self,
        objective: XGBoostObjective = "count:poisson",
        n_estimators: int = 500,
        early_stopping_rounds: int = 30,
        scale_numeric: bool = False,
        use_early_stopping: bool = True,
        schema: FeatureSchema = DEMAND_FEATURE_SCHEMA_V1,
    ) -> None:
        if n_estimators < 1:
            raise ValueError("n_estimators must be positive.")

        if early_stopping_rounds < 1:
            raise ValueError("early_stopping_rounds must be positive.")

        self.objective = objective
        self.n_estimators = n_estimators
        self.early_stopping_rounds = early_stopping_rounds
        self.scale_numeric = scale_numeric
        self.schema = schema

        self._use_early_stopping = use_early_stopping

    @property
    def uses_early_stopping(self) -> bool:
        """Return whether backtesting should use early stopping."""

        return self._use_early_stopping

    def create_preprocessor(self) -> XGBoostPreprocessor:
        """Create a fresh XGBoost preprocessor."""

        return XGBoostPreprocessor(
            schema=self.schema,
            scale_numeric=self.scale_numeric,
        )

    def fit(
        self,
        train: SupervisedDataset,
    ) -> XGBRegressor:
        """Fit a model without early stopping."""

        model = self._create_model()
        model.fit(
            train.features,
            train.target,
        )

        return model

    def fit_with_early_stopping(
        self,
        train: SupervisedDataset,
        validation: SupervisedDataset,
    ) -> XGBRegressor:
        """Fit a model while monitoring validation MAE."""

        model = self._create_model()
        model.set_params(
            early_stopping_rounds=self.early_stopping_rounds,
        )
        model.fit(
            train.features,
            train.target,
            eval_set=[
                (
                    validation.features,
                    validation.target,
                )
            ],
            verbose=False,
        )

        return model

    def predict(
        self,
        model: XGBRegressor,
        features: pd.DataFrame,
    ) -> np.ndarray:
        """Return non-negative demand predicitons."""

        predictions = model.predict(features)

        return np.clip(
            predictions,
            a_min=0,
            a_max=None,
        )

    def selected_iteration(
        self,
        model: XGBRegressor,
    ) -> int:
        """Return the tree count selected by early stopping ."""

        best_iteration = getattr(model, "best_iteration", None)

        if best_iteration is None:
            raise RuntimeError("The model was not fitted with early stopping.")

        return int(best_iteration) + 1

    def _create_model(self) -> XGBRegressor:
        """Create an unfitted XGBoost regressor."""

        return XGBRegressor(
            n_estimators=self.n_estimators,
            learning_rate=0.05,
            max_depth=4,
            subsample=0.8,
            colsample_bytree=0.8,
            objective=self.objective,
            enable_categorical=True,
            tree_method="hist",
            eval_metric="mae",
            random_state=42,
        )
