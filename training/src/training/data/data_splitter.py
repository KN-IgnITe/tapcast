from typing import Iterator, Tuple
import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

from training.data.mock_data_generator import DayKey


class DataSplitter:
    """
    Splits data into chronological train and test dataframes,
    based on a specified test size percentage.
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

    def get_final_test_split(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Cuts last x of data for final test set"""
        df_sorted = df.sort_values(by=DayKey.DATE).reset_index(drop=True)

        split_idx = int(len(df_sorted) * (1 - self.test_size))

        train_val_df = df_sorted.iloc[:split_idx].copy()
        test_df = df_sorted.iloc[split_idx:].copy()

        return train_val_df, test_df

    def get_walk_forward_splits(
        self, df: pd.DataFrame
    ) -> Iterator[Tuple[np.ndarray, np.ndarray]]:
        """
        Generates the forward window of data,
        expects sorted data by date
        """
        tscv = TimeSeriesSplit(n_splits=self.n_splits)

        return tscv.split(df)
