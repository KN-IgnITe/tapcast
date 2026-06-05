from typing import Iterator, Tuple
import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

from training.data.mock_data_generator import DayKey


class DataSplitter:
    """
    Splits data into chronological train and test dataframes
    based on unique dates, rather than idividual rows
    ensuring a single date is never fractured between splits.
    """

    test_size: float
    n_splits: int

    def __init__(self, test_size: float = 0.15, n_splits: int = 5):
        """
        :param test_size: Proportion of the dataset
            to include in the test split (between 0 and 1).
        :param n_splits: Number of splits to create.
        """
        self.test_size = test_size
        self.n_splits = n_splits

    def _get_sorted_unique_dates(self, df: pd.DataFrame) -> pd.Series:
        """Extracts and sorts unique dates from the dataframe."""
        date_col = DayKey.DATE.value

        dates = pd.to_datetime(df[date_col])

        return pd.Series(dates.unique()).sort_values().reset_index(drop=True)

    def get_final_test_split(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Cuts last X% of unique dates for final test set"""

        date_col = DayKey.DATE.value

        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])

        unique_dates = self._get_sorted_unique_dates(df)

        split_idx = int(len(unique_dates) * (1 - self.test_size))

        if split_idx == len(unique_dates):
            split_idx = max(0, len(unique_dates) - 1)

        split_date = unique_dates.iloc[split_idx]

        train_val_df = df[df[date_col] < split_date].copy()
        test_df = df[df[date_col] >= split_date].copy()

        return (train_val_df.reset_index(drop=True), test_df.reset_index(drop=True))

    def get_walk_forward_splits(
        self, df: pd.DataFrame
    ) -> Iterator[Tuple[np.ndarray, np.ndarray]]:
        """
        Generates the forward window of data using unique dates,
        yielding arrays of row indices corresponding to train/test subsets.
        """

        date_col = DayKey.DATE.value

        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])

        unique_dates = self._get_sorted_unique_dates(df)
        date_series = df[date_col].to_numpy()

        tscv = TimeSeriesSplit(n_splits=self.n_splits)

        for train_date_idx, test_date_idx in tscv.split(unique_dates):
            train_dates = unique_dates.iloc[train_date_idx]
            test_dates = unique_dates.iloc[test_date_idx]

            train_idx = np.where(np.isin(date_series, train_dates))[0]
            test_idx = np.where(np.isin(date_series, test_dates))[0]

            yield train_idx, test_idx
