from abc import abstractmethod
from typing import Protocol, runtime_checkable

import pandas as pd

from ml_common.model.feature_schema import FeatureSchema


@runtime_checkable
class FeaturePreprocessor(Protocol):
    """Transform model features into estimator-compatible data."""

    schema: FeatureSchema

    @abstractmethod
    def fit_transform(self, features: pd.DataFrame) -> pd.DataFrame: ...

    @abstractmethod
    def transform(self, features: pd.DataFrame) -> pd.DataFrame: ...
