from typing import Generic, TypeVar

import pandas as pd

from training.data.data_splitter import DataSplitter
from training.features.temporal_matrix_builder import TemporalMatrixBuilder
from training.models.early_stopping_strategy import EarlyStoppingTrainingStrategy
from training.models.model_trainer import ModelTrainer

ModelT = TypeVar("ModelT")


class EarlyStoppingSelector(Generic[ModelT]):
    """Select a final iteration count without using the final test set."""

    def __init__(
        self,
        strategy: EarlyStoppingTrainingStrategy[ModelT],
        splitter: DataSplitter,
        matrix_builder: TemporalMatrixBuilder,
    ) -> None:
        self._stategy = strategy
        self._splitter = splitter
        self._matrix_builder = matrix_builder

    def select(
        self,
        raw_train_validation: pd.DataFrame,
    ) -> int:
        raw_inner_train, raw_early_stop = self._splitter.get_inner_validation_split(
            raw_train_validation
        )

        train_matrix, early_stop_matrix = self._matrix_builder.build_train_evaluation(
            raw_train=raw_inner_train,
            raw_evaluation=raw_early_stop,
        )

        trainer = ModelTrainer(self._stategy)
        trainer.fit_with_early_stopping(
            train_matrix=train_matrix,
            validation_matrix=early_stop_matrix,
        )

        return self._stategy.selected_iteration(trainer.model)
