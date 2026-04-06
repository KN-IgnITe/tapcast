
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
import pandas as pd

class DataProcessor:
    """ DataProcessor is responsible for preprocessing(scalinh, encoding) the data before it is fed into the model."""

    numeric_features: list[str]
    categorical_features: list[str]
    passthrough_features: list[str]
    target_col: str
    preprocessor: ColumnTransformer
    is_fitted: bool

    def __init__(self):
        self.numeric_features = [
            "avg_temp", "temp_amplitude", "rain", 
            "yesterday_demand", "week_ago_demand"
        ]

        self.categorical_features = ["day_of_week", "category", "PLU"]

        self.passthrough_features = ["is_working", "is_next_day_working"]

        self.target_col = "amount"

        self.preprocessor = ColumnTransformer(
            transformers=[
                ("num", StandardScaler(), self.numeric_features),
                ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), self.categorical_features),
            ],
            remainder="passthrough" # Passthrough the remaining features (is_working, is_next_day_working
        )

        self.is_fitted = False

    def fit_transform(self, train_df: pd.DataFrame) -> pd.DataFrame:
        """ Transform the training data using the defined preprocessor"""
        
        transformed_array = self.preprocessor.fit_transform(train_df)
        self.is_fitted = True

        columns = self._get_feature_names()

        return pd.DataFrame(transformed_array, columns=columns, index=train_df.index)
    
    def transform(self, test_df: pd.DataFrame) -> pd.DataFrame:
        """ Transform the test data using the fitted preprocessor"""
        if not self.is_fitted:
            raise RuntimeError("Preprocessor must be fitted before calling transform. Call fit_transform on training data first.")
        
        transformed_array = self.preprocessor.transform(test_df)

        columns = self._get_feature_names()

        return pd.DataFrame(transformed_array, columns=columns, index=test_df.index)
    
    def _get_feature_names(self) -> list:
        """ Get the feature names after transformation for both numeric and categorical features"""
        numerical_cols = self.numeric_features
        categorical_cols = self.preprocessor.named_transformers_["cat"].get_feature_names_out(self.categorical_features).tolist()

        all_original_cols = self.preprocessor.feature_names_in_
        
        remainder_cols = [
            col for col in all_original_cols 
            if col not in self.categorical_features and col not in self.numeric_features
        ]
        return numerical_cols + categorical_cols + remainder_cols