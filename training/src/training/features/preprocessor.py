import pandas as pd
from pandas.api.types import CategoricalDtype
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from training.data.columns import PipelineKey
from training.data.mock_data_generator import ArticleKey, DayKey


class ModelPreprocessor:
    """
    Prepare training_matrix for linear and xgboost models.
    """

    target_col = PipelineKey.TARGET_DEMAND.value
    date_col = DayKey.DATE.value
    categorical_cols = [
        ArticleKey.PLU.value,
        ArticleKey.CATEGORY.value,
    ]

    linear_preprocessor: ColumnTransformer | None
    xgboost_category_dtypes: dict[str, CategoricalDtype]

    def __init__(self, scale_numeric: bool = False) -> None:

        self.scale_numeric: bool = scale_numeric

        self.linear_preprocessor: ColumnTransformer | None = None

        self.xgboost_category_dtypes: dict[str, CategoricalDtype] = {}

        self.xgboost_numeric_scaler: StandardScaler | None = None
        self.xgboost_numeric_cols: list[str] = []

    def split_features_target(
        self,
        df: pd.DataFrame,
    ) -> tuple[pd.DataFrame, pd.Series]:
        """Split training matrix into features and target."""

        data = df.copy()

        y = data[self.target_col].astype(float)
        X = data.drop(columns=[self.target_col, self.date_col])

        return X, y

    def fit_transform_for_xgboost(
        self, df: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.Series]:
        """Fit preprocessing and transform features for XGBoost model."""

        X, y = self.split_features_target(df)

        self.xgboost_category_dtypes = {}

        for col in self.categorical_cols:
            category_dtype = CategoricalDtype(
                categories=sorted(X[col].dropna().unique())
            )

            self.xgboost_category_dtypes[col] = category_dtype
            X[col] = X[col].astype(category_dtype)

        self.xgboost_numeric_cols = [
            col for col in X.columns if col not in self.categorical_cols
        ]

        self.xgboost_numeric_scaler = None

        if self.scale_numeric:
            self.xgboost_numeric_scaler = StandardScaler()

            scaled_values = self.xgboost_numeric_scaler.fit_transform(
                X[self.xgboost_numeric_cols]
            )

            X[self.xgboost_numeric_cols] = scaled_values

        return X, y

    def transform_for_xgboost(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
        """Transform features for XGBoost using fitted category dtypes"""

        if not self.xgboost_category_dtypes:
            raise RuntimeError("Call fit_transform_for_xgboost first.")

        X, y = self.split_features_target(df)

        for col in self.categorical_cols:
            category_dtype = self.xgboost_category_dtypes[col]
            known_categories = category_dtype.categories

            known_category_mask = X[col].isin(known_categories)
            X[col] = X[col].mask(~known_category_mask)
            X[col] = X[col].astype(category_dtype)

        if self.scale_numeric:
            if self.xgboost_numeric_scaler is None:
                raise RuntimeError("XGBoost numeric sclaer has not been fitted.")

            X[self.xgboost_numeric_cols] = self.xgboost_numeric_scaler.transform(
                X[self.xgboost_numeric_cols]
            )

        return X, y

    def fit_transform_for_linear(
        self, df: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.Series]:
        """Fit preprocessing and transform features for Ridge/Linear models."""

        X, y = self.split_features_target(df)

        numeric_cols = [col for col in X.columns if col not in self.categorical_cols]

        numeric_steps: list[tuple[str, object]] = [
            (
                "imputer",
                SimpleImputer(strategy="median", keep_empty_features=True),
            )
        ]

        if self.scale_numeric:
            numeric_steps.append(("scaler", StandardScaler()))

        numeric_transformer = Pipeline(numeric_steps)

        self.linear_preprocessor = ColumnTransformer(
            transformers=[
                ("num", numeric_transformer, numeric_cols),
                (
                    "cat",
                    OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                    self.categorical_cols,
                ),
            ],
            remainder="drop",
        )

        transformed = self.linear_preprocessor.fit_transform(X)
        feature_names = self.linear_preprocessor.get_feature_names_out()

        return pd.DataFrame(transformed, columns=feature_names, index=X.index), y

    def transform_for_linear(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
        """Transform features for Ridge/Linear models using fitted preprocessor."""

        if self.linear_preprocessor is None:
            raise ValueError("Preprocessor has not been fitted yet.")

        X, y = self.split_features_target(df)

        transformed = self.linear_preprocessor.transform(X)
        feature_names = self.linear_preprocessor.get_feature_names_out()

        return pd.DataFrame(transformed, columns=feature_names, index=X.index), y
