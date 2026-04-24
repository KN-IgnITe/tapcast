import numpy as np
import pandas as pd
import pytest
from training.data.data_splitter import DataSplitter
from training.data.mock_data_generator import DayKey


@pytest.fixture
def dummy_dataframe() -> pd.DataFrame:
    dates = pd.date_range(start="2023-01-01", periods=100)
    return pd.DataFrame({DayKey.DATE: dates, "value": range(100)})


def test_get_final_test_split(dummy_dataframe: pd.DataFrame) -> None:
    splitter = DataSplitter(test_size=0.2)
    train_df, test_df = splitter.get_final_test_split(dummy_dataframe)

    assert len(train_df) == 80
    assert len(test_df) == 20
    assert train_df[DayKey.DATE].max() < test_df[DayKey.DATE].min()


def test_get_walk_forward_splits(dummy_dataframe: pd.DataFrame) -> None:
    splitter = DataSplitter(n_splits=5)

    splits = list(splitter.get_walk_forward_splits(dummy_dataframe))

    assert len(splits) == 5

    train_idx_0, test_idx0 = splits[0]

    assert isinstance(train_idx_0, np.ndarray)
    assert isinstance(test_idx0, np.ndarray)

    assert train_idx_0[-1] < test_idx0[0]
