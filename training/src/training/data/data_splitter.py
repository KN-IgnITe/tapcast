from typing import Tuple

import pandas as pd
class DataSplitter:
    """Splits data into chronological train and test dataframes based on a specified test size percentage."""

    test_size: float

    def __init__(self, test_size: float = 0.2):
        """
        :param test_size: Proportion of the dataset to include in the test split (between 0 and 1).
        """
        self.test_size = test_size

    def split(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        df_sorted = df.sort_values(by="date").reset_index(drop=True)

        split_idx = int(len(df_sorted) * (1 - self.test_size))

        train_df = df_sorted.iloc[:split_idx].copy()
        test_df = df_sorted.iloc[split_idx:].copy()

        return train_df, test_df
