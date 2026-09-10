from typing import Generic, TypeVar, cast

import numpy as np
import pandas as pd
from ml_common.model.preprocessing.base import FeaturePreprocessor

from training.data.columns import PipelineKey
from training.models.early_stopping_strategy import (
    EarlyStoppingTrainingStrategy,
)
from training.models.training_strategy import (
    ModelTrainingStrategy,
    SupervisedDataset,
)

ModelT = TypeVar("ModelT")


class ModelTrainer(Generic[ModelT]):
    """Train and evaluate a demand model using an injected strategy."""

    def __init__(
        self,
        strategy: ModelTrainingStrategy[ModelT],
    ) -> None:
        self._strategy = strategy
        self._model: ModelT | None = None
        self._preprocessor: FeaturePreprocessor | None = None

    def fit(
        self,
        train_matrix: pd.DataFrame,
    ) -> "ModelTrainer[ModelT]":
        """Fit preprocessing and model on a training matrix."""

        preprocessor, train_dataset = self._fit_dataset(train_matrix)

        model = self._strategy.fit(train_dataset)
        self._preprocessor = preprocessor
        self._model = model

        return self

    def fit_with_early_stopping(
        self,
        train_matrix: pd.DataFrame,
        validation_matrix: pd.DataFrame,
    ) -> "ModelTrainer[ModelT]":
        """Fit a model while monitoring validation data."""

        strategy = self._require_early_stopping_strategy()

        preprocessor, train_dataset = self._fit_dataset(train_matrix)
        validation_dataset = self._transform_dataset(
            validation_matrix,
            preprocessor,
        )

        model = strategy.fit_with_early_stopping(
            train_dataset,
            validation_dataset,
        )

        self._preprocessor = preprocessor
        self._model = model

        return self

    def predict(
        self,
        matrix: pd.DataFrame,
    ) -> np.ndarray:
        """Predict demand using the fitted model and preprocessor."""

        model = self.model
        preprocessor = self.preprocessor

        features = preprocessor.transform(matrix)

        return self._strategy.predict(
            model,
            features,
        )

    @property
    def model(self) -> ModelT:
        if self._model is None:
            raise RuntimeError("The model has not been fitted.")

        return self._model

    @property
    def preprocessor(self) -> FeaturePreprocessor:
        if self._preprocessor is None:
            raise RuntimeError("The preprocessor has not been fitted.")

        return self._preprocessor

    def _fit_dataset(
        self,
        matrix: pd.DataFrame,
    ) -> tuple[FeaturePreprocessor, SupervisedDataset]:
        """Fit preprocessing and build a supervised dataset."""

        preprocessor = self._strategy.create_preprocessor()
        features = preprocessor.fit_transform(matrix)
        target = self._extract_target(matrix)

        dataset = SupervisedDataset(features=features, target=target)

        return preprocessor, dataset

    def _transform_dataset(
        self,
        matrix: pd.DataFrame,
        preprocessor: FeaturePreprocessor,
    ) -> SupervisedDataset:
        """Transform features without fitting preprocessing again."""

        features = preprocessor.transform(matrix)
        target = self._extract_target(matrix)

        return SupervisedDataset(
            features=features,
            target=target,
        )

    @staticmethod
    def _extract_target(matrix: pd.DataFrame) -> pd.Series:
        """Extract target demand from a prepared matrix."""

        target_column = PipelineKey.TARGET_DEMAND.value

        if target_column not in matrix.columns:
            raise ValueError(f"Missing target column: {target_column}")

        return matrix[target_column].astype(float).copy()

    def _require_early_stopping_strategy(
        self,
    ) -> EarlyStoppingTrainingStrategy[ModelT]:

        if not isinstance(
            self._strategy,
            EarlyStoppingTrainingStrategy,
        ):
            raise TypeError("Selected strategy doest not support early stopping.")

        return cast(
            EarlyStoppingTrainingStrategy[ModelT],
            self._strategy,
        )
