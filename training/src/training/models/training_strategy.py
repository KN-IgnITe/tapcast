from abc import abstractmethod
from dataclasses import dataclass
from typing import ClassVar, Protocol, TypeVar

import numpy as np
import pandas as pd
from ml_common.model.model_kind import ModelKind
from ml_common.model.preprocessing.base import FeaturePreprocessor

ModelT = TypeVar("ModelT")


@dataclass(frozen=True)
class SupervisedDataset:
    """Contain model features and their corresponding target values."""

    features: pd.DataFrame
    target: pd.Series


class ModelTrainingStrategy(Protocol[ModelT]):
    """Define operations supported by every demand model."""

    model_kind: ClassVar[ModelKind]

    @property
    @abstractmethod
    def uses_early_stopping(self) -> bool:
        """Indicate whether backtesting requires early-stop validation."""
        ...

    @abstractmethod
    def create_preprocessor(self) -> FeaturePreprocessor:
        """Create a fresh preprocessor."""
        ...

    @abstractmethod
    def fit(
        self,
        train: SupervisedDataset,
    ) -> ModelT:
        """Create and fit a model."""
        ...

    @abstractmethod
    def predict(
        self,
        model: ModelT,
        features: pd.DataFrame,
    ) -> np.ndarray:
        """Predict values in the original target scale."""
        ...
