import numpy as np
import pandas as pd
import pytest
from training.data.data_splitter import DataSplitter
from training.data.mock_data_generator import DayKey


@pytest.fixture
def multi_plu_dataframe() -> pd.DataFrame:
    rows = []

    for date in pd.date_range("2023-01-01", periods=10):
        for plu in [101, 102, 103]:
            rows.append(
                {
                    DayKey.DATE.value: date,
                    "PLU": plu,
                    "value": len(rows),
                }
            )

    return pd.DataFrame(rows)


@pytest.fixture
def dummy_dataframe() -> pd.DataFrame:
    dates = pd.date_range(start="2023-01-01", periods=100)
    return pd.DataFrame({DayKey.DATE.value: dates, "value": range(100)})


def test_get_final_test_split(dummy_dataframe: pd.DataFrame) -> None:
    splitter = DataSplitter(test_size=0.2)
    train_df, test_df = splitter.get_final_test_split(dummy_dataframe)

    assert len(train_df) == 80
    assert len(test_df) == 20
    assert train_df[DayKey.DATE.value].max() < test_df[DayKey.DATE.value].min()


def test_get_walk_forward_splits(dummy_dataframe: pd.DataFrame) -> None:
    splitter = DataSplitter(n_splits=5)

    splits = list(splitter.get_walk_forward_splits(dummy_dataframe))

    assert len(splits) == 5

    for train_idx, val_idx in splits:
        assert isinstance(train_idx, np.ndarray)
        assert isinstance(val_idx, np.ndarray)

        train_dates = set(dummy_dataframe.iloc[train_idx][DayKey.DATE.value])
        val_dates = set(dummy_dataframe.iloc[val_idx][DayKey.DATE.value])

        assert train_dates.isdisjoint(val_dates)
        assert max(train_dates) < min(val_dates)


def test_get_final_test_split_does_not_split_same_date(
    multi_plu_dataframe: pd.DataFrame,
) -> None:
    splitter = DataSplitter(test_size=0.2)

    train_df, test_df = splitter.get_final_test_split(multi_plu_dataframe)

    train_dates = set(train_df[DayKey.DATE.value])
    test_dates = set(test_df[DayKey.DATE.value])

    assert train_dates.isdisjoint(test_dates)
    assert train_df[DayKey.DATE.value].max() < test_df[DayKey.DATE.value].min()

    assert train_df[DayKey.DATE.value].nunique() == 8
    assert test_df[DayKey.DATE.value].nunique() == 2

    assert len(train_df) == 24
    assert len(test_df) == 6


def test_get_walk_forward_splits_do_not_split_same_date(
    multi_plu_dataframe: pd.DataFrame,
) -> None:
    splitter = DataSplitter(n_splits=3)

    splits = list(splitter.get_walk_forward_splits(multi_plu_dataframe))

    assert len(splits) == 3

    for train_idx, val_idx in splits:
        train_df = multi_plu_dataframe.iloc[train_idx]
        val_df = multi_plu_dataframe.iloc[val_idx]

        train_dates = set(train_df[DayKey.DATE.value])
        val_dates = set(val_df[DayKey.DATE.value])

        assert train_dates.isdisjoint(val_dates)
        assert train_df[DayKey.DATE.value].max() < (val_df[DayKey.DATE.value].min())

        for date in val_dates:
            rows_for_date = multi_plu_dataframe[
                multi_plu_dataframe[DayKey.DATE.value] == date
            ]

            assert len(rows_for_date) == (
                len(val_df[val_df[DayKey.DATE.value] == date])
            )
