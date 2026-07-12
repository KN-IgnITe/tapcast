from enum import Enum
from typing import Literal

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from xgboost import XGBRegressor

from training.data.data_splitter import DataSplitter
from training.evaluation.metrics import RegressionMetrics
from training.features.preprocessor import ModelPreprocessor
from training.features.temporal_matrix_builder import TemporalMatrixBuilder

from training.data.mock_data_generator import ArticleKey, DayKey
from training.evaluation.backtest import BacktestResult
from training.data.columns import PipelineKey

XGBoostObjective = Literal[
    "count:poisson",
    "reg:tweedie",
]


class ModelType(Enum):
    LOG_LIN = "log_lin"
    XGBOOST = "xgboost"


class ModelTrainer:
    """Initializes, trains and evaluates model in walkForward approach"""

    def __init__(
        self,
        model_type: ModelType,
        scale_numeric: bool | None = None,
        xgboost_objective: XGBoostObjective = "count:poisson",
        early_stopping_rounds: int = 30,
        n_estimators: int = 500,
    ) -> None:

        self.model_type = model_type
        self.xgboost_objective = xgboost_objective
        self.early_stopping_rounds = early_stopping_rounds
        self.n_estimators = n_estimators

        default_scaling = model_type == ModelType.LOG_LIN
        self.scale_numeric = default_scaling if scale_numeric is None else scale_numeric

        self.preprocessor: ModelPreprocessor | None = None
        self.model: Ridge | XGBRegressor | None = None

    def _get_model(self) -> Ridge | XGBRegressor:
        """Create a new model instance."""

        if self.model_type == ModelType.LOG_LIN:
            return Ridge()

        if self.model_type == ModelType.XGBOOST:
            return XGBRegressor(
                n_estimators=self.n_estimators,
                learning_rate=0.05,
                max_depth=4,
                subsample=0.8,
                colsample_bytree=0.8,
                objective=self.xgboost_objective,
                enable_categorical=True,
                tree_method="hist",
                eval_metric="mae",
                random_state=42,
            )

        raise ValueError(
            f"Unsupported model type: {self.model_type}. Choose 'log_lin' or 'xgboost'."
        )

    def _prepare_data(
        self, train_df: pd.DataFrame, eval_df: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
        """Prepare training and evaluation data for selected model."""

        preprocessor = ModelPreprocessor(scale_numeric=self.scale_numeric)
        self.preprocessor = preprocessor

        if self.model_type == ModelType.XGBOOST:
            X_train, y_train = self.preprocessor.fit_transform_for_xgboost(train_df)
            X_eval, y_eval = self.preprocessor.transform_for_xgboost(eval_df)
        else:
            X_train, y_train = self.preprocessor.fit_transform_for_linear(train_df)
            X_eval, y_eval = preprocessor.transform_for_linear(eval_df)

        return X_train, y_train, X_eval, y_eval

    def _train_and_predict(
        self, X_train: pd.DataFrame, y_train: pd.Series, X_eval: pd.DataFrame
    ) -> np.ndarray:
        """Train model and predict evaluation data."""

        y_for_training = y_train

        if self.model_type == ModelType.LOG_LIN:
            y_for_training = np.log1p(y_train)

        self.model = self._get_model()
        self.model.fit(X_train, y_for_training)

        predictions = self.model.predict(X_eval)

        if self.model_type == ModelType.LOG_LIN:
            predictions = np.expm1(predictions)

        return np.clip(predictions, a_min=0, a_max=None)

    def _calculate_metrics(
        self, y_true: pd.Series, predictions: np.ndarray
    ) -> dict[str, float]:
        """Calculate global regression metrics."""

        return RegressionMetrics.calculate(y_true, predictions)

    def _run_pipeline(
        self,
        train_df: pd.DataFrame,
        eval_df: pd.DataFrame,
    ) -> tuple[dict[str, float], np.ndarray]:
        """Prepare data, train model and evaluate predictions."""

        X_train, y_train, X_eval, y_eval = self._prepare_data(train_df, eval_df)

        predictions = self._train_and_predict(
            X_train,
            y_train,
            X_eval,
        )

        metrics = self._calculate_metrics(y_eval, predictions)

        return metrics, predictions

    def _run_xgboost_fold(
        self,
        inner_train: pd.DataFrame,
        early_stop_val: pd.DataFrame,
        outer_val: pd.DataFrame,
    ) -> tuple[dict[str, float], np.ndarray]:
        """Train with early stopping and evaluate on untouch outer validation."""

        model, preprocessor = self._fit_xgboost_with_early_stopping(
            inner_train,
            early_stop_val,
        )
        X_outer, y_outer = preprocessor.transform_for_xgboost(outer_val)

        predictions = np.clip(
            model.predict(X_outer),
            a_min=0,
            a_max=None,
        )

        metrics = RegressionMetrics.calculate(
            y_outer,
            predictions,
        )

        return metrics, predictions

    def _fit_xgboost_with_early_stopping(
        self,
        train_df: pd.DataFrame,
        early_stop_df: pd.DataFrame,
    ) -> tuple[XGBRegressor, ModelPreprocessor]:
        """Fit XGBoost while monitoring a chronological validation set."""

        preprocessor = ModelPreprocessor(scale_numeric=self.scale_numeric)
        self.preprocessor = preprocessor

        X_train, y_train = preprocessor.fit_transform_for_xgboost(train_df)
        X_early, y_early = preprocessor.transform_for_xgboost(early_stop_df)

        model = self._get_model()

        if not isinstance(model, XGBRegressor):
            raise TypeError("Early stopping requires XGBRegressor.")

        model.set_params(early_stopping_rounds=self.early_stopping_rounds)
        model.fit(
            X_train,
            y_train,
            eval_set=[(X_early, y_early)],
            verbose=False,
        )

        self.model = model

        return model, preprocessor

    def select_final_tree_count(
        self,
        raw_train_val_df: pd.DataFrame,
        splitter: DataSplitter,
        matrix_builder: TemporalMatrixBuilder,
    ) -> int:
        """Select boosting rounds using the latest train-val history."""

        if self.model_type != ModelType.XGBOOST:
            raise TypeError("Tree count selection requires XGBoost.")

        raw_inner_train, raw_early_stop = splitter.get_inner_validation_split(
            raw_train_val_df
        )
        inner_train, early_stop = matrix_builder.build_train_evaluation(
            raw_inner_train,
            raw_early_stop,
        )

        model, _ = self._fit_xgboost_with_early_stopping(
            inner_train,
            early_stop,
        )

        return model.best_iteration + 1

    def _evaluate_fold(
        self,
        train_fold: pd.DataFrame,
        val_fold: pd.DataFrame,
        splitter: DataSplitter,
        matrix_builder: TemporalMatrixBuilder,
    ) -> tuple[dict[str, float], np.ndarray, pd.DataFrame]:
        """Build leakage-safe matrices and evaluate one outer fold."""

        if self.model_type == ModelType.XGBOOST:
            raw_inner_train, raw_early_stop = splitter.get_inner_validation_split(
                train_fold
            )

            inner_train, early_stop, outer_val = (
                matrix_builder.build_early_stopping_fold(
                    raw_inner_train,
                    raw_early_stop,
                    val_fold,
                )
            )

            metrics, predictions = self._run_xgboost_fold(
                inner_train,
                early_stop,
                outer_val,
            )

            return metrics, predictions, outer_val

        train_matrix, val_matrix = matrix_builder.build_train_evaluation(
            train_fold,
            val_fold,
        )
        metrics, predictions = self._run_pipeline(
            train_matrix,
            val_matrix,
        )

        return metrics, predictions, val_matrix

    def _build_prediction_frame(
        self,
        val_fold: pd.DataFrame,
        predictions: np.ndarray,
        fold_number: int,
    ) -> pd.DataFrame:
        """Attach predictions to outer-validation context."""

        output = val_fold[
            [
                DayKey.DATE.value,
                ArticleKey.PLU.value,
                ArticleKey.CATEGORY.value,
                PipelineKey.TARGET_DEMAND.value,
            ]
        ].copy()

        output[PipelineKey.PREDICTION.value] = predictions
        output[PipelineKey.BACKTEST_FOLD.value] = fold_number

        return output

    def _build_backtest_result(
        self,
        fold_metrics: list[dict[str, float]],
        prediction_frames: list[pd.DataFrame],
    ) -> BacktestResult:
        """Build global and grouped reports."""

        predictions = pd.concat(
            prediction_frames,
            ignore_index=True,
        )

        target = PipelineKey.TARGET_DEMAND.value
        predicted = PipelineKey.PREDICTION.value

        return BacktestResult(
            global_metrics=RegressionMetrics.calculate(
                predictions[target],
                predictions[predicted],
            ),
            fold_metrics=fold_metrics,
            per_plu=RegressionMetrics.calculate_grouped(
                predictions,
                target,
                predicted,
                ArticleKey.PLU.value,
            ),
            per_category=RegressionMetrics.calculate_grouped(
                predictions,
                target,
                predicted,
                ArticleKey.CATEGORY.value,
            ),
            predictions=predictions,
        )

    def run_walk_forward_training(
        self,
        raw_train_val_df: pd.DataFrame,
        splitter: DataSplitter,
        matrix_builder: TemporalMatrixBuilder,
    ) -> BacktestResult:
        """Run fold-aware backtesting starting from raw history."""

        fold_metrics: list[dict[str, float]] = []
        prediction_frames: list[pd.DataFrame] = []

        for fold_number, (train_idx, val_idx) in enumerate(
            splitter.get_walk_forward_splits(raw_train_val_df),
            start=1,
        ):
            train_fold = raw_train_val_df.iloc[train_idx].copy()
            val_fold = raw_train_val_df.iloc[val_idx].copy()

            metrics, predictions, val_matrix = self._evaluate_fold(
                train_fold,
                val_fold,
                splitter,
                matrix_builder,
            )

            fold_metrics.append(metrics)

            prediction_frames.append(
                self._build_prediction_frame(
                    val_matrix,
                    predictions,
                    fold_number,
                )
            )

        return self._build_backtest_result(
            fold_metrics,
            prediction_frames,
        )

    def evaluate_on_test(
        self, train_df: pd.DataFrame, test_df: pd.DataFrame
    ) -> dict[str, float]:
        """Evaluate selected configuration on untouched test data."""

        metrics, _ = self._run_pipeline(
            train_df,
            test_df,
        )

        return metrics

    def fit_final(
        self,
        train_df: pd.DataFrame,
    ) -> "ModelTrainer":
        """Fit the final model without validation or early stopping."""

        preprocessor = ModelPreprocessor(scale_numeric=self.scale_numeric)

        if self.model_type == ModelType.XGBOOST:
            X_train, y_train = preprocessor.fit_transform_for_xgboost(train_df)
            y_for_training = y_train
        else:
            X_train, y_train = preprocessor.fit_transform_for_linear(train_df)
            y_for_training = np.log1p(y_train)

        model = self._get_model()
        model.fit(X_train, y_for_training)

        self.preprocessor = preprocessor
        self.model = model

        return self
