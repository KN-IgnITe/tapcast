from enum import Enum
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

from training.data.data_splitter import DataSplitter
from training.features.preprocessor import DataProcessor

from training.data.mock_data_generator import ArticleKey, DayKey


class ModelType(str, Enum):
    LOG_LIN = "log_lin"
    XGBOOST = "xgboost"


class ModelTrainer:
    """Initializes, trains and evaluates model in walkForward approach"""

    model_type: ModelType

    def __init__(self, model_type: ModelType) -> None:
        """
        :param model_type: Choose algorithm "xgboost" or "log_lin"
        """
        self.model_type = model_type

    def _get_model(self) -> Ridge | XGBRegressor:
        """Model factory"""
        if self.model_type == ModelType.LOG_LIN:
            # Classical linear model with regularization
            return Ridge(random_state=42)

        elif self.model_type == ModelType.XGBOOST:
            # tree model
            return XGBRegressor(
                n_estimators=500,
                learning_rate=0.05,
                max_depth=4,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
            )
        else:
            raise ValueError(
                f"Unsupported model type: {self.model_type}. "
                "Choose 'log_lin' or 'xgboost'."
            )

    def _prepare_data(
        self, train_df: pd.DataFrame, eval_df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
        """Preprocess the data and split into X and Y"""
        preprocessor = DataProcessor()

        X_train_proc = preprocessor.fit_transform(train_df)
        X_eval_proc = preprocessor.transform(eval_df)

        target_col = ArticleKey.AMOUNT.value
        date_col = DayKey.DATE.value

        drop_cols = [target_col, date_col]

        X_train = X_train_proc.drop(columns=drop_cols).astype(float)
        y_train = X_train_proc[target_col].astype(float)

        X_eval = X_eval_proc.drop(columns=drop_cols).astype(float)
        y_eval = X_eval_proc[target_col].astype(float)

        return X_train, y_train, X_eval, y_eval

    def _train_and_predict(
        self, X_train: pd.DataFrame, y_train: pd.Series, X_eval: pd.DataFrame
    ) -> np.ndarray:
        """Handles target transformation, model training and prediction"""

        if self.model_type == ModelType.LOG_LIN:
            y_train = np.log1p(y_train)

        model = self._get_model()
        model.fit(X_train, y_train)

        preds = model.predict(X_eval)

        # If log_lin model, apply log transformation to the target variable
        if self.model_type == ModelType.LOG_LIN:
            preds = np.expm1(preds)

        preds = np.clip(preds, a_min=0, a_max=None)

        return preds

    def _calculate_metrics(
        self, y_true: pd.Series, preds: np.ndarray
    ) -> Dict[str, float]:
        """Calculate and returns evaluation metrics for the predictions"""
        # Defence against potential issues with zero values in y_true
        # Calculate sum of absolute errors
        sum_errors = np.sum(np.abs(y_true - preds))

        # 2. Calculate sum of actual values.
        sum_actuals = np.sum(y_true)

        # 3. Calculate WMAPE,
        # adding a small constant to the denominator to avoid division by zero
        wmape = sum_errors / (sum_actuals + 1e-10)

        return {
            "MAE": float(mean_absolute_error(y_true, preds)),
            "RMSE": float(np.sqrt(mean_squared_error(y_true, preds))),
            "R2": float(r2_score(y_true, preds)),
            "MAPE": float(wmape),
        }

    def _run_pipeline(
        self, train_df: pd.DataFrame, eval_df: pd.DataFrame
    ) -> Tuple[Dict[str, float], np.ndarray]:
        """Runs the full pipeline of data preparation, model training and evaluation"""
        X_train, y_train, X_eval, y_eval = self._prepare_data(train_df, eval_df)
        preds = self._train_and_predict(X_train, y_train, X_eval)
        metrics = self._calculate_metrics(y_eval, preds)

        return metrics, preds

    def run_walk_forward_training(
        self, train_val_df: pd.DataFrame, splitter: DataSplitter
    ) -> float:
        """Runs walk-forward training and evaluation, returns avg MAE for folds"""
        all_metrics: Dict[str, List[float]] = {
            "MAE": [],
            "RMSE": [],
            "R2": [],
            "MAPE": [],
        }

        for fold, (train_idx, val_idx) in enumerate(
            splitter.get_walk_forward_splits(train_val_df)
        ):
            train_fold = train_val_df.iloc[train_idx]
            val_fold = train_val_df.iloc[val_idx]

            metrics, _ = self._run_pipeline(train_fold, val_fold)

            for key in all_metrics:
                all_metrics[key].append(metrics[key])

            print(
                f"Fold {fold + 1} | MAE: {metrics['MAE']:.4f} | "
                f"RMSE: {metrics['RMSE']:.4f} | R2: {metrics['R2']:.4f} | "
                f"MAPE: {metrics['MAPE']:.4f}"
            )

        # Summarize results across folds
        print("-" * 30)
        for metrics_name, values in all_metrics.items():
            mean_value = np.mean(values)
            print(f"Average {metrics_name} across folds: {mean_value:.4f}")

        return float(np.mean(all_metrics["MAE"]))

    def evaluate_on_test(self, train_df: pd.DataFrame, test_df: pd.DataFrame) -> float:
        """Train model on whole train data and evaluate on test set"""
        metrics, _ = self._run_pipeline(train_df, test_df)

        print(
            f"Test set evaluation | MAE: {metrics['MAE']:.4f} | "
            f"RMSE: {metrics['RMSE']:.4f} | R2: {metrics['R2']:.4f} | "
            f"MAPE: {metrics['MAPE']:.4f}"
        )

        return metrics["MAE"]
