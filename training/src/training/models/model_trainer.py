import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error, r2_score
from xgboost import XGBRegressor
from sklearn.linear_model import Ridge
from data.data_splitter import DataSplitter
from features.preprocessor import DataProcessor


class ModelTrainer:
    """Initializes, trains and evaluates model in walkForward approach"""

    model_type = str

    def __init__(self, model_type: str = "log_lin"):
        """
        :param model_type: Choose algorithm "xgboost" or "log_lin"
        """
        self.model_type = model_type

    def _get_model(self):
        """Model factory"""
        if self.model_type == "log_lin":
            # Classical linear model with regularization
            return Ridge(random_state=42)
        
        elif self.model_type == "xgboost":
            # tree model
            return XGBRegressor(
                n_estimators=500,
                learning_rate=0.05,
                max_depth=4,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42
                )
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}. Choose 'log_lin' or 'xgboost'.")
        
    def run_walk_forward_training(self, train_val_df: pd.DataFrame, splitter: DataSplitter) -> float:   

        mae_scores = []
        rmse_scores = []
        r2_scores = []
        mape_scores = []

        for fold, (train_idx, val_idx) in enumerate(splitter.get_walk_forward_splits(train_val_df)):
            # Split the data into training and validation sets for the current fold
            train_fold = train_val_df.iloc[train_idx]
            val_fold = train_val_df.iloc[val_idx]

            preprocessor = DataProcessor()

            # Transform the training and validation data using the preprocessor
            X_train_proc = preprocessor.fit_transform(train_fold)
            X_val_proc = preprocessor.transform(val_fold)

            # Extract the target variable
            drop_cols = ["amount", "date"]  
            X_train = X_train_proc.drop(columns=drop_cols).astype(float)
            y_train = X_train_proc["amount"].astype(float)

            X_val = X_val_proc.drop(columns=drop_cols).astype(float)
            y_val = X_val_proc["amount"].astype(float)

            # If log_lin model, apply log transformation to the target variable
            if self.model_type == "log_lin":
                y_train = np.log1p(y_train)

            # Inicialize and train the model
            model = self._get_model()
            model.fit(X_train, y_train)    

            # predict on unknown set val
            preds = model.predict(X_val)

            # Reverse logarithm
            if self.model_type == "log_lin":
                preds = np.expm1(preds)

            # Clip predictions to be non-negative
            preds = np.clip(preds, a_min = 0, a_max = None)    

            mae = mean_absolute_error(y_val, preds)
            rmse = np.sqrt(mean_squared_error(y_val, preds))
            r2 = r2_score(y_val, preds)
            mape = mean_absolute_percentage_error(y_val, preds)

            mae_scores.append(mae)
            rmse_scores.append(rmse)
            r2_scores.append(r2)
            mape_scores.append(mape)

            print(f"Fold {fold + 1} | MAE: {mae:.4f} | RMSE: {rmse:.4f} | R2: {r2:.4f} | MAPE: {mape:.4f}")

        # Summarize results across folds
        mean_mae = np.mean(mae_scores)
        mean_rmse = np.mean(rmse_scores)
        mean_r2 = np.mean(r2_scores)
        mean_mape = np.mean(mape_scores)

        print(f"Average MAE across folds: {mean_mae:.4f}")
        print(f"Average RMSE across folds: {mean_rmse:.4f}")
        print(f"Average R2 across folds: {mean_r2:.4f}")
        print(f"Average MAPE across folds: {mean_mape:.4f}")

        return mean_mae    
    
    def evaluate_on_test(self, train_df: pd.DataFrame, test_df: pd.DataFrame) -> float:
        """Train model on whole train data and evaluate on test set"""
        preprocessor = DataProcessor()

        X_train_proc = preprocessor.fit_transform(train_df)
        X_test_proc = preprocessor.transform(test_df)

        drop_cols = ["amount", "date"]  
        X_train = X_train_proc.drop(columns=drop_cols).astype(float)
        y_train = X_train_proc["amount"].astype(float)

        X_test = X_test_proc.drop(columns=drop_cols).astype(float)
        y_test = X_test_proc["amount"].astype(float)

        if self.model_type == "log_lin":
            y_train = np.log1p(y_train)

        model = self._get_model()
        model.fit(X_train, y_train)

        preds = model.predict(X_test)

        if self.model_type == "log_lin":
            preds = np.expm1(preds)

        preds = np.clip(preds, a_min=0, a_max=None)

        mae = mean_absolute_error(y_test, preds)
        rmse = np.sqrt(mean_squared_error(y_test, preds))
        r2 = r2_score(y_test, preds)
        mape = mean_absolute_percentage_error(y_test, preds)

        print(f"Test set evaluation | MAE: {mae:.4f} | RMSE: {rmse:.4f} | R2: {r2:.4f} | MAPE: {mape:.4f}")

        return mae