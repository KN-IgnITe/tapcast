import pandas as pd
from sklearn.base import TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ml_common.model.feature_schema import FeatureSchema
from ml_common.model.preprocessing.base import FeaturePreprocessor


class RidgePreprocessor(FeaturePreprocessor):
    """Prepare model features for a Ridge estimator."""

    def __init__(
        self,
        schema: FeatureSchema,
        scale_numeric: bool = True,
    ) -> None:
        self.schema = schema
        self.scale_numeric = scale_numeric

        self._column_transformer: ColumnTransformer | None = None

        self._is_fitted = False

    def fit_transform(
        self,
        features: pd.DataFrame,
    ) -> pd.DataFrame:
        """Learn preprocessing artifacts and transform training features."""

        transformed = self.schema.select_and_validate(features)

        self._is_fitted = False
        self._column_transformer = None

        numeric_columns = [
            column
            for column in transformed.columns
            if column not in self.schema.categorical_columns
        ]

        numeric_steps: list[tuple[str, TransformerMixin]] = [
            (
                "imputer",
                SimpleImputer(
                    strategy="median",
                    keep_empty_features=True,
                ),
            )
        ]

        if self.scale_numeric:
            numeric_steps.append(
                (
                    "scaler",
                    StandardScaler(),
                )
            )

        numeric_transformer = Pipeline(
            steps=numeric_steps,
        )

        column_transformer = ColumnTransformer(
            transformers=[
                (
                    "num",
                    numeric_transformer,
                    numeric_columns,
                ),
                (
                    "cat",
                    OneHotEncoder(
                        handle_unknown="ignore",
                        sparse_output=False,
                    ),
                    list(self.schema.categorical_columns),
                ),
            ],
            remainder="drop",
        )

        transformed_values = column_transformer.fit_transform(transformed)
        feature_names = column_transformer.get_feature_names_out()

        self._column_transformer = column_transformer
        self._is_fitted = True

        return pd.DataFrame(
            transformed_values,
            columns=feature_names,
            index=transformed.index,
        )

    def transform(
        self,
        features: pd.DataFrame,
    ) -> pd.DataFrame:
        """Transform features using previously fitted artifacts."""

        if not self._is_fitted or self._column_transformer is None:
            raise RuntimeError("Call fit_transform before transform.")

        transformed = self.schema.select_and_validate(features)

        transformed_values = self._column_transformer.transform(transformed)

        feature_names = self._column_transformer.get_feature_names_out()

        return pd.DataFrame(
            transformed_values,
            columns=feature_names,
            index=transformed.index,
        )
