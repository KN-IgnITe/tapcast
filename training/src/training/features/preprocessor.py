import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from training.data.mock_data_generator import ArticleKey, DayKey, WeatherKey


class DataProcessor:
    """
    DataProcessor is responsible for:
    preprocessing(scaling, encoding) the data before it is fed into the model.
    """

    numeric_features: list[str]
    categorical_features: list[str]
    target_col: str
    preprocessor: ColumnTransformer
    is_fitted: bool

    def __init__(self) -> None:
        self.numeric_features = [
            WeatherKey.AVG_TEMP.value,
            WeatherKey.TEMP_AMPLITUDE.value,
            WeatherKey.RAIN.value,
            ArticleKey.YESTERDAY_DEMAND.value,
            ArticleKey.WEEK_AGO_DEMAND.value,
        ]

        self.categorical_features = [
            DayKey.DAY_OF_WEEK.value,
            ArticleKey.CATEGORY.value,
            ArticleKey.PLU.value,
        ]

        self.target_col = ArticleKey.DEMAND.value

        self.preprocessor = ColumnTransformer(
            transformers=[
                ("num", StandardScaler(), self.numeric_features),
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

        train_df_logged = self._apply__log_transformer(train_df)

        transformed_array = self.preprocessor.fit_transform(train_df_logged)
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

        test_df_logged = self._apply__log_transformer(test_df)

        transformed_array = self.preprocessor.transform(test_df_logged)

        columns = self._get_feature_names()

        return pd.DataFrame(transformed_array, columns=columns, index=test_df.index)

    def _get_feature_names(self) -> list[str]:
        """Get the feature names after transformation"""
        numerical_cols = self.numeric_features
        cat_transformer = self.preprocessor.named_transformers_["cat"]

        categorical_cols = cat_transformer.get_feature_names_out(
            self.categorical_features
        ).tolist()

        all_original_cols = self.preprocessor.feature_names_in_

        remainder_cols = [
            col
            for col in all_original_cols
            if col not in self.categorical_features and col not in self.numeric_features
        ]

        return numerical_cols + categorical_cols + remainder_cols

    def _apply__log_transformer(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        yest_key = ArticleKey.YESTERDAY_DEMAND.value
        week_key = ArticleKey.WEEK_AGO_DEMAND.value

        df[yest_key] = np.log1p(df[yest_key].astype(float))
        df[week_key] = np.log1p(df[week_key].astype(float))

        return df
