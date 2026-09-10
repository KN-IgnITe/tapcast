import pandas as pd
from pandas import CategoricalDtype
from sklearn.preprocessing import StandardScaler

from ml_common.model.feature_schema import FeatureSchema
from ml_common.model.preprocessing.base import FeaturePreprocessor


class XGBoostPreprocessor(FeaturePreprocessor):
    """Prepare model feautres for a XGBoost estimator"""

    def __init__(
        self,
        schema: FeatureSchema,
        scale_numeric: bool = False,
    ) -> None:
        self.schema = schema
        self.scale_numeric = scale_numeric

        self._category_dtypes: dict[str, CategoricalDtype] = {}
        self._numeric_cols: list[str] = []
        self._numeric_scaler: StandardScaler | None = None

        self._is_fitted = False

    def fit_transform(self, features: pd.DataFrame) -> pd.DataFrame:
        """Learn preprocessing artifacts and transform training features."""

        transformed = self.schema.select_and_validate(features)

        self._is_fitted = False
        self._category_dtypes = {}
        self._numeric_cols = []
        self._numeric_scaler = None

        for column in self.schema.categorical_columns:
            category_dtype = CategoricalDtype(
                categories=sorted(transformed[column].dropna().unique())
            )

            self._category_dtypes[column] = category_dtype
            transformed[column] = transformed[column].astype(category_dtype)

        self._numeric_cols = [
            column
            for column in transformed.columns
            if column not in self.schema.categorical_columns
        ]

        if self.scale_numeric and self._numeric_cols:
            self._numeric_scaler = StandardScaler()

            scaled_values = self._numeric_scaler.fit_transform(
                transformed[self._numeric_cols]
            )

            transformed[self._numeric_cols] = scaled_values

        self._is_fitted = True

        return transformed

    def transform(self, features: pd.DataFrame) -> pd.DataFrame:
        """Transform features using previously fitted artifacts."""

        if not self._is_fitted:
            raise RuntimeError("Call fit_transform before transform.")

        transformed = self.schema.select_and_validate(features)

        for column in self.schema.categorical_columns:
            category_dtype = self._category_dtypes[column]
            known_categories = category_dtype.categories

            known_category_mask = transformed[column].isin(known_categories)

            transformed[column] = transformed[column].mask(~known_category_mask)
            transformed[column] = transformed[column].astype(category_dtype)

        if self.scale_numeric and self._numeric_cols:
            if self._numeric_scaler is None:
                raise RuntimeError("XGBoost numeric scaler has not been fitted.")

            scaled_values = self._numeric_scaler.transform(
                transformed[self._numeric_cols]
            )

            transformed[self._numeric_cols] = scaled_values

        return transformed
