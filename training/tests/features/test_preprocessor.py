import numpy as np
import pandas as pd
import pytest
from pandas.api.types import CategoricalDtype
from training.data.columns import PipelineKey
from training.data.mock_data_generator import ArticleKey, DayKey, WeatherKey
from training.features.preprocessor import ModelPreprocessor


@pytest.fixture
def dummy_train_data() -> pd.DataFrame:
    """Create a small training matrix."""
    return pd.DataFrame(
        {
            DayKey.DATE.value: pd.to_datetime(
                ["2026-01-01", "2026-01-02", "2026-01-03"]
            ),
            ArticleKey.PLU.value: [101, 102, 101],
            ArticleKey.CATEGORY.value: [1, 2, 1],
            WeatherKey.AVG_TEMP.value: [10.0, 15.0, 20.0],
            PipelineKey.DEMAND_LAG_14D.value: [8.0, 12.0, 16.0],
            PipelineKey.TARGET_DEMAND.value: [10, 20, 30],
        }
    )


@pytest.fixture
def dummy_test_data() -> pd.DataFrame:
    """Create validation data containing unknown categories."""
    return pd.DataFrame(
        {
            DayKey.DATE.value: pd.to_datetime(["2026-01-04"]),
            ArticleKey.PLU.value: [999],
            ArticleKey.CATEGORY.value: [9],
            WeatherKey.AVG_TEMP.value: [12.0],
            PipelineKey.DEMAND_LAG_14D.value: [9.0],
            PipelineKey.TARGET_DEMAND.value: [11],
        }
    )


def test_split_features_target_removes_target_and_date(
    dummy_train_data: pd.DataFrame,
) -> None:
    processor = ModelPreprocessor()

    X, y = processor.split_features_target(dummy_train_data)

    assert PipelineKey.TARGET_DEMAND.value not in X.columns
    assert DayKey.DATE.value not in X.columns
    assert y.tolist() == [10.0, 20.0, 30.0]
    assert y.dtype == float


def test_split_features_target_does_not_modify_input(
    dummy_train_data: pd.DataFrame,
) -> None:
    processor = ModelPreprocessor()
    original = dummy_train_data.copy(deep=True)

    processor.split_features_target(dummy_train_data)

    pd.testing.assert_frame_equal(dummy_train_data, original)


def test_fit_transform_for_xgboost_creates_categorical_columns(
    dummy_train_data: pd.DataFrame,
) -> None:
    processor = ModelPreprocessor()

    X, _ = processor.fit_transform_for_xgboost(dummy_train_data)

    for column in processor.categorical_cols:
        assert isinstance(X[column].dtype, CategoricalDtype)
        assert X[column].dtype == processor.xgboost_category_dtypes[column]


def test_trainsform_for_xgboost_requrires_fit(dummy_test_data: pd.DataFrame) -> None:
    processor = ModelPreprocessor()

    with pytest.raises(
        RuntimeError,
        match="Call fit_transform_for_xgboost first",
    ):
        processor.transform_for_xgboost(dummy_test_data)


def test_xgboost_transform_uses_categories_learned_from_training(
    dummy_train_data: pd.DataFrame, dummy_test_data: pd.DataFrame
) -> None:
    processor = ModelPreprocessor()
    processor.fit_transform_for_xgboost(dummy_train_data)

    X_test, _ = processor.transform_for_xgboost(dummy_test_data)

    plu_col = ArticleKey.PLU.value
    category_col = ArticleKey.CATEGORY.value

    assert X_test[plu_col].isna().all()
    assert X_test[category_col].isna().all()
    assert X_test[plu_col].dtype == processor.xgboost_category_dtypes[plu_col]


def test_xgboost_preprocessor_scales_numeric_features(
    dummy_train_data: pd.DataFrame,
) -> None:
    processor = ModelPreprocessor(scale_numeric=True)

    X, _ = processor.fit_transform_for_xgboost(dummy_train_data)

    avg_temp_col = WeatherKey.AVG_TEMP.value

    assert np.isclose(X[avg_temp_col].mean(), 0.0)
    assert isinstance(
        X[ArticleKey.PLU.value].dtype,
        CategoricalDtype,
    )


def test_fit_transform_for_linear_creates_numeric_features(
    dummy_train_data: pd.DataFrame,
) -> None:
    processor = ModelPreprocessor()

    X, y = processor.fit_transform_for_linear(dummy_train_data)

    assert len(X) == len(dummy_train_data)
    assert len(y) == len(dummy_train_data)
    assert all(np.issubdtype(dtype, np.number) for dtype in X.dtypes)
    assert any(column.startswith("cat_") for column in X.columns)


def test_linear_preprocessor_imputes_missing_numeric_features(
    dummy_train_data: pd.DataFrame,
) -> None:
    processor = ModelPreprocessor()
    data_with_missing_lag = dummy_train_data.copy()
    data_with_missing_lag.loc[0, PipelineKey.DEMAND_LAG_14D.value] = np.nan

    X, _ = processor.fit_transform_for_linear(data_with_missing_lag)

    assert not X.isna().any().any()


def test_transform_for_linear_requires_fit(
    dummy_test_data: pd.DataFrame,
) -> None:
    processor = ModelPreprocessor()

    with pytest.raises(
        ValueError,
        match="Preprocessor has not been fitted yet",
    ):
        processor.transform_for_linear(dummy_test_data)


def test_linear_transform_ignores_unknown_categories(
    dummy_train_data: pd.DataFrame,
    dummy_test_data: pd.DataFrame,
) -> None:
    processor = ModelPreprocessor()

    X_train, _ = processor.fit_transform_for_linear(dummy_train_data)
    X_test, _ = processor.transform_for_linear(dummy_test_data)

    assert list(X_test.columns) == list(X_train.columns)

    plu_prefix = f"cat__{ArticleKey.PLU.value}_"
    plu_columns = [column for column in X_test.columns if column.startswith(plu_prefix)]

    assert (X_test[plu_columns].iloc[0] == 0).all()


def test_linear_preprocessor_scales_numeric_features(
    dummy_train_data: pd.DataFrame,
) -> None:
    processor = ModelPreprocessor(scale_numeric=True)

    X, _ = processor.fit_transform_for_linear(dummy_train_data)

    avg_temp_col = f"num__{WeatherKey.AVG_TEMP.value}"

    assert np.isclose(X[avg_temp_col].mean(), 0.0)
