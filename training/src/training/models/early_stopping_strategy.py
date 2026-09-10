from abc import abstractmethod
from typing import Protocol, TypeVar, runtime_checkable

from training.models.training_strategy import (
    ModelTrainingStrategy,
    SupervisedDataset,
)

ModelT = TypeVar("ModelT")


@runtime_checkable
class EarlyStoppingTrainingStrategy(
    ModelTrainingStrategy[ModelT],
    Protocol[ModelT],
):
    """Extend a model strategy with early stopping support."""

    @abstractmethod
    def fit_with_early_stopping(
        self,
        train: SupervisedDataset,
        validation: SupervisedDataset,
    ) -> ModelT:
        """Fit a model while monitoring validation data."""

        ...

    @abstractmethod
    def selected_iteration(
        self,
        model: ModelT,
    ) -> int:
        """Return the iteration count selected by early stopping."""

        ...
