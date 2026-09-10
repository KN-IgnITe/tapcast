from typing import Generic, TypeVar

import numpy as np
import pandas as pd

from training.data.columns import PipelineKey
from training.data.data_splitter import DataSplitter
from training.data.mock_data_generator import ArticleKey, DayKey
from training.evaluation.backtest import BacktestResult
from training.evaluation.metrics import RegressionMetrics
from training.features.temporal_matrix_builder import TemporalMatrixBuilder
from training.models.model_trainer import ModelTrainer
from training.models.training_strategy import ModelTrainingStrategy

ModelT = TypeVar("ModelT")


class ModelBacktester(Generic[ModelT]):
    """Evaluate a moddel strategy using chronological walk-forward folds."""

    def __init__(
        self,
        strategy: ModelTrainingStrategy[ModelT],
        splitter: DataSplitter,
        matrix_builder: TemporalMatrixBuilder,
    ) -> None:

        self._strategy = strategy
        self._splitter = splitter
        self._matrix_builder = matrix_builder

    def run(
        self,
        raw_train_validation: pd.DataFrame,
    ) -> BacktestResult:
        """Run all folds and aggregate their predictions and matrics"""

        prediction_frames: list[pd.DataFrame] = []
        fold_metrics: list[dict[str, float]] = []

        splits = self._splitter.get_walk_forward_splits(raw_train_validation)

        for fold_num, (train_indices, validation_indices) in enumerate(
            splits,
            start=1,
        ):
            raw_train = raw_train_validation.iloc[train_indices].copy()
            raw_validation = raw_train_validation.iloc[validation_indices].copy()

            validation_matrix, predictions = self._evaluate_fold(
                raw_train=raw_train,
                raw_validation=raw_validation,
            )

            prediction_frame = self._build_prediction_frame(
                validation_matrix=validation_matrix,
                predictions=predictions,
                fold_number=fold_num,
            )

            fold_metrics.append(
                RegressionMetrics.calculate(
                    y_true=prediction_frame[PipelineKey.TARGET_DEMAND.value],
                    y_pred=prediction_frame[PipelineKey.PREDICTION.value],
                )
            )
            prediction_frames.append(prediction_frame)

        if not prediction_frames:
            raise ValueError("Backtesting did not produce any folds.")

        all_predictions = pd.concat(
            prediction_frames,
            ignore_index=True,
        )

        return self._build_result(
            predictions=all_predictions,
            fold_metrics=fold_metrics,
        )

    def _evaluate_fold(
        self,
        raw_train: pd.DataFrame,
        raw_validation: pd.DataFrame,
    ) -> tuple[pd.DataFrame, np.ndarray]:
        """Train a fresh model and predict the outer validation period."""

        if self._strategy.uses_early_stopping:
            return self._evaluate_early_stopping_fold(
                raw_train,
                raw_validation,
            )

        return self._evaluate_standard_fold(
            raw_train,
            raw_validation,
        )

    def _evaluate_standard_fold(
        self,
        raw_train: pd.DataFrame,
        raw_validation: pd.DataFrame,
    ) -> tuple[pd.DataFrame, np.ndarray]:
        """Evaluate strategy a standard way."""

        train_matrix, validation_matrix = self._matrix_builder.build_train_evaluation(
            raw_train=raw_train,
            raw_evaluation=raw_validation,
        )

        trainer = ModelTrainer(self._strategy)
        trainer.fit(train_matrix)

        predictions = trainer.predict(validation_matrix)

        return validation_matrix, predictions

    def _evaluate_early_stopping_fold(
        self,
        raw_train: pd.DataFrame,
        raw_validation: pd.DataFrame,
    ) -> tuple[pd.DataFrame, np.ndarray]:
        """Evaluate strategy using early stopping validation."""

        raw_inner_train, raw_early_stop = self._splitter.get_inner_validation_split(
            raw_train
        )

        (
            inner_train_matrix,
            early_stop_matrix,
            outer_validation_matrix,
        ) = self._matrix_builder.build_early_stopping_fold(
            raw_inner_train=raw_inner_train,
            raw_early_stop=raw_early_stop,
            raw_outer_validation=raw_validation,
        )

        trainer = ModelTrainer(self._strategy)
        trainer.fit_with_early_stopping(
            train_matrix=inner_train_matrix, validation_matrix=early_stop_matrix
        )

        predictions = trainer.predict(outer_validation_matrix)

        return outer_validation_matrix, predictions

    @staticmethod
    def _build_prediction_frame(
        validation_matrix: pd.DataFrame,
        predictions: np.ndarray,
        fold_number: int,
    ) -> pd.DataFrame:

        if predictions.ndim != 1 or len(predictions) != len(validation_matrix):
            raise ValueError("Expected one prediction per validation row.")

        columns = [
            DayKey.DATE.value,
            ArticleKey.PLU.value,
            ArticleKey.CATEGORY.value,
            PipelineKey.TARGET_DEMAND.value,
        ]
        frame = validation_matrix.loc[:, columns].copy()
        frame[PipelineKey.PREDICTION.value] = predictions
        frame[PipelineKey.BACKTEST_FOLD.value] = fold_number

        return frame

    @staticmethod
    def _build_result(
        predictions: pd.DataFrame,
        fold_metrics: list[dict[str, float]],
    ) -> BacktestResult:
        target_column = PipelineKey.TARGET_DEMAND.value
        prediction_column = PipelineKey.PREDICTION.value

        return BacktestResult(
            global_metrics=RegressionMetrics.calculate(
                y_true=predictions[target_column],
                y_pred=predictions[prediction_column],
            ),
            fold_metrics=fold_metrics,
            per_plu=RegressionMetrics.calculate_grouped(
                df=predictions,
                y_true_col=target_column,
                y_pred_col=prediction_column,
                group_col=ArticleKey.PLU.value,
            ),
            per_category=RegressionMetrics.calculate_grouped(
                df=predictions,
                y_true_col=target_column,
                y_pred_col=prediction_column,
                group_col=ArticleKey.CATEGORY.value,
            ),
            predictions=predictions,
        )
