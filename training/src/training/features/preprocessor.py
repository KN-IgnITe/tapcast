import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from training.data.mock_data_generator import ArticleKey, DayKey, WeatherKey


class DataProcessor:
    """
    DataProcessor is responsible for:
    preprocessing(scaling, encoding) the data before it is fed into the model.
    """

    scale_numeric: bool
    demand_features: list[str]
    weather_features: list[str]
    categorical_features: list[str]
    preprocessor: ColumnTransformer
    is_fitted: bool

    def __init__(self, scale_numeric: bool = False) -> None:

        self.scale_numeric = scale_numeric

        self.demand_features = [
            ArticleKey.YESTERDAY_DEMAND.value,
            ArticleKey.WEEK_AGO_DEMAND.value,
        ]

        self.weather_features = [
            WeatherKey.AVG_TEMP.value,
            WeatherKey.TEMP_AMPLITUDE.value,
            WeatherKey.RAIN.value,
        ]

        self.categorical_features = [
            DayKey.DAY_OF_WEEK.value,
            ArticleKey.CATEGORY.value,
            ArticleKey.PLU.value,
        ]

        if self.scale_numeric:
            demand_transformer = Pipeline(
                steps=[
                    ("log1p", FunctionTransformer(np.log1p, validate=False)),
                    ("scaler", StandardScaler()),
                ]
            )

            weather_transformer = StandardScaler()

        else:
            demand_transformer = "passthrough"
            weather_transformer = "passthrough"

        self.preprocessor = ColumnTransformer(
            transformers=[
                ("demand_num", demand_transformer, self.demand_features),
                ("weather_num", weather_transformer, self.weather_features),
                (
                    "cat",
                    OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                    self.categorical_features,
                ),
            ],
            remainder="passthrough",
        )

        self.is_fitted = False

    def fit_transform(self, train_df: pd.DataFrame) -> pd.DataFrame:
        """Transform the training data using the defined preprocessor"""

        # Hard rest and conversion of columns to string from Enum
        train_df = train_df.copy()
        train_df.columns = [getattr(c, "value", str(c)) for c in train_df.columns]

        transformed_array = self.preprocessor.fit_transform(train_df)
        self.is_fitted = True

        columns = self._get_feature_names()

        return pd.DataFrame(transformed_array, columns=columns, index=train_df.index)

    def transform(self, test_df: pd.DataFrame) -> pd.DataFrame:
        """Transform the test data using the fitted preprocessor"""
        if not self.is_fitted:
            raise RuntimeError("Call fit_transform on the training data first")

        # Hard rest and conversion of columns to string from Enum
        test_df = test_df.copy()
        test_df.columns = [getattr(c, "value", str(c)) for c in test_df.columns]

        transformed_array = self.preprocessor.transform(test_df)

        columns = self._get_feature_names()

        return pd.DataFrame(transformed_array, columns=columns, index=test_df.index)

    def _get_feature_names(self) -> list[str]:
        """Get the feature names after transformation"""
        numerical_cols = self.demand_features + self.weather_features
        cat_transformer = self.preprocessor.named_transformers_["cat"]

        categorical_cols = cat_transformer.get_feature_names_out(
            self.categorical_features
        ).tolist()

        all_original_cols = self.preprocessor.feature_names_in_

        remainder_cols = [
            col
            for col in all_original_cols
            if col not in self.categorical_features
            and col not in self.demand_features
            and col not in self.weather_features
        ]

        return numerical_cols + categorical_cols + remainder_cols
