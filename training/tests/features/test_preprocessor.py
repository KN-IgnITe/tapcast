import numpy as np
import pandas as pd
import pytest
from training.data.mock_data_generator import ArticleKey, DayKey, WeatherKey
from training.features.preprocessor import DataProcessor


@pytest.fixture
def dummy_train_data() -> pd.DataFrame:
    """Fixture to create dummy training data for testing."""
    return pd.DataFrame(
        {
            WeatherKey.AVG_TEMP.value: [10.0, 15.0, 20.0],
            WeatherKey.TEMP_AMPLITUDE.value: [2.0, 3.0, 4.0],
            WeatherKey.RAIN.value: [0.0, 1.5, 0.0],
            ArticleKey.YESTERDAY_DEMAND.value: [10, 0, 50],
            ArticleKey.WEEK_AGO_DEMAND.value: [15, 5, 45],
            DayKey.DAY_OF_WEEK.value: [1, 2, 1],
            ArticleKey.CATEGORY.value: [1, 2, 3],
            ArticleKey.PLU.value: [101, 102, 101],
            ArticleKey.DEMAND.value: [12, 2, 55],
            DayKey.DATE.value: ["2023-01-01", "2023-01-02", "2023-01-03"],
        }
    )


@pytest.fixture
def dummy_test_data() -> pd.DataFrame:
    """
    Fixture to create dummy test data for testing.
    This data includes an unknown PLU (999) to test if
    handle_unknown="ignore" in OneHotEncoder works correctly.
    """
    return pd.DataFrame(
        {
            WeatherKey.AVG_TEMP.value: [12.0],
            WeatherKey.TEMP_AMPLITUDE.value: [2.5],
            WeatherKey.RAIN.value: [0.0],
            ArticleKey.YESTERDAY_DEMAND.value: [12],
            ArticleKey.WEEK_AGO_DEMAND.value: [14],
            DayKey.DAY_OF_WEEK.value: [1],
            ArticleKey.CATEGORY.value: [1],
            ArticleKey.PLU.value: [999],
            ArticleKey.DEMAND.value: [15],
            DayKey.DATE.value: ["2023-01-04"],
        }
    )


def test_transform_raises_error_if_not_fitted(dummy_train_data: pd.DataFrame) -> None:
    """Test that transform raises an error if fit_transform has not been called."""
    processor = DataProcessor()
    with pytest.raises(
        RuntimeError, match="Call fit_transform on the training data first"
    ):
        processor.transform(dummy_train_data)


def test_apply_log_transformer_calculates_log1p_correctly(
    dummy_train_data: pd.DataFrame,
) -> None:
    """
    Test that _apply__log_transformer correctly applies
    np.log1p to the target column.
    """
    processor = DataProcessor()

    df_logged = processor._apply__log_transformer(dummy_train_data)

    yest_key = ArticleKey.YESTERDAY_DEMAND.value

    expected_val = np.log1p(10.0)
    actual_val = df_logged[yest_key].iloc[0]

    assert np.isclose(expected_val, actual_val)

    assert np.isclose(0.0, df_logged[yest_key].iloc[1])


def test_fit_transform_creates_correct_columns(dummy_train_data: pd.DataFrame) -> None:
    """Sprawdza End-to-End proces uczenia preprocesora na zbiorze treningowym."""
    processor = DataProcessor()

    proc_df = processor.fit_transform(dummy_train_data)

    assert processor.is_fitted is True

    # remainder passthrough collumns should be present
    assert ArticleKey.DEMAND.value in proc_df.columns
    assert DayKey.DATE.value in proc_df.columns

    # one-hot encoded columns should be present
    plu_cols = [col for col in proc_df.columns if str(ArticleKey.PLU.value) in col]
    assert len(plu_cols) == 2


def test_transform_ignores_unknown_categories(
    dummy_train_data: pd.DataFrame, dummy_test_data: pd.DataFrame
) -> None:
    """
    Sprawdza, czy model poprawnie ignoruje nowe,
    niewidziane wcześnie kategorie (handle_unknown='ignore').
    """
    processor = DataProcessor()

    processor.fit_transform(dummy_train_data)

    # test data contains PLU=999, should be no errror
    test_proc_df = processor.transform(dummy_test_data)

    # all should be 0.0 for PLU_999 because it's an unknown category
    plu_101_col = f"{ArticleKey.PLU.value}_101"

    if plu_101_col in test_proc_df.columns:
        assert test_proc_df[plu_101_col].iloc[0] == 0.0
