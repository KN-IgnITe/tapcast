from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class FeatureSchema:
    """Define the ordered feature contract expected by a model."""

    name: str
    version: int
    columns: tuple[str, ...]
    categorical_columns: tuple[str, ...]

    def __post_init__(self) -> None:
        unknown_categorical = set(self.categorical_columns) - set(self.columns)

        if unknown_categorical:
            raise ValueError(
                "Categorical columns are missing from the feature schema: "
                f"{sorted(unknown_categorical)}"
            )

        if len(self.columns) != len(set(self.columns)):
            raise ValueError("Feature schema contains duplicate columns.")

    def select_and_validate(
        self,
        features: pd.DataFrame,
    ) -> pd.DataFrame:
        """Validate required features and return them in the expected order."""

        missing_columns = set(self.columns) - set(features.columns)

        if missing_columns:
            raise ValueError(f"Missing model features: {sorted(missing_columns)}")

        return features.loc[:, list(self.columns)].copy()
