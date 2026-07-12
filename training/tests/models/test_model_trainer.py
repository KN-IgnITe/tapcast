import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import Ridge

from training.data.columns import PipelineKey
from training.data.data_splitter import DataSplitter
from training.data.mock_data_generator import ArticleKey, DayKey, WeatherKey
from training.evaluation.backtest import BacktestResult
from training.features.history_cleaner import HistoryCleanerConfig
from training.features.temporal_matrix_builder import TemporalMatrixBuilder
from training.models.model_trainer import ModelTrainer, ModelType
from xgboost import XGBRegressor


@pytest.fixture
def dummy_pipeline_data() -> pd.DataFrame:
    """Fixture to create dummy data for testing the entire pipeline."""

    np.random.seed(42)
    dates = pd.date_range(start="2023-01-01", periods=20).repeat(2)
    row_count = len(dates)

    return pd.DataFrame(
        {
            DayKey.DATE.value: dates,
            ArticleKey.PLU.value: [101, 102] * 20,
            ArticleKey.CATEGORY.value: [1, 2] * 20,
            WeatherKey.AVG_TEMP.value: np.random.rand(row_count) * 20,
            PipelineKey.DEMAND_LAG_14D.value: np.random.randint(
                10,
                50,
                row_count,
            ),
            PipelineKey.TARGET_DEMAND.value: np.random.randint(
                10,
                100,
                row_count,
            ),
        }
    )


@pytest.fixture
def dummy_raw_data() -> pd.DataFrame:
    """Create chronological raw history for fold-aware backtesting."""

    dates = pd.date_range(start="2023-01-01", periods=50).repeat(2)
    plu_values = [101, 102] * 50

    return pd.DataFrame(
        {
            DayKey.DATE.value: dates,
            ArticleKey.PLU.value: plu_values,
            ArticleKey.CATEGORY.value: [1, 2] * 50,
            ArticleKey.DEMAND.value: [10, 20, 12, 18, 14, 22, 16, 24, 18, 26] * 10,
            DayKey.DAY_OF_WEEK.value: dates.isocalendar().day.to_numpy(),
            DayKey.IS_WORKING.value: (dates.weekday < 5).astype(int),
            DayKey.IS_NEXT_DAY_WORKING.value: (
                (dates + pd.Timedelta(days=1)).weekday < 5
            ).astype(int),
            WeatherKey.AVG_TEMP.value: np.linspace(5.0, 20.0, len(dates)),
            WeatherKey.TEMP_AMPLITUDE.value: np.full(len(dates), 4.0),
            WeatherKey.RAIN.value: np.zeros(len(dates)),
        }
    )


def test_get_model_returns_correct_instances() -> None:
    """Checks if factory method returns correct model"""
    trainer_log = ModelTrainer(ModelType.LOG_LIN)

    assert isinstance(trainer_log._get_model(), Ridge)

    trainer_xgb = ModelTrainer(ModelType.XGBOOST)
    assert isinstance(trainer_xgb._get_model(), XGBRegressor)


def test_run_walk_forward_training_executes_succesfully(
    dummy_raw_data: pd.DataFrame,
) -> None:
    """Checks if the entire pipeline runs without errors and returns metrics"""
    trainer = ModelTrainer(ModelType.XGBOOST, early_stopping_rounds=2)
    splitter = DataSplitter(n_splits=2)
    matrix_builder = TemporalMatrixBuilder(
        cleaning_config=HistoryCleanerConfig(winsorized_quantile=1.0)
    )

    result = trainer.run_walk_forward_training(
        dummy_raw_data,
        splitter,
        matrix_builder,
    )

    assert isinstance(result, BacktestResult)
    assert result.global_metrics["MAE"] >= 0.0
    assert not result.per_plu.empty
    assert not result.per_category.empty
    assert PipelineKey.BACKTEST_FOLD.value in result.predictions.columns


def test_evaluate_on_test_executes_succesfully(
    dummy_pipeline_data: pd.DataFrame,
) -> None:
    """Checks final evaluation on test with xgboost model"""
    trainer = ModelTrainer(ModelType.XGBOOST)

    split_date = pd.Timestamp("2023-01-16")
    train_df = dummy_pipeline_data[dummy_pipeline_data[DayKey.DATE.value] < split_date]
    test_df = dummy_pipeline_data[dummy_pipeline_data[DayKey.DATE.value] >= split_date]

    metrics = trainer.evaluate_on_test(train_df, test_df)

    assert isinstance(metrics, dict)
    assert metrics["MAE"] >= 0.0


def test_select_final_tree_count_returns_valid_boosting_rounds(
    dummy_raw_data: pd.DataFrame,
) -> None:
    trainer = ModelTrainer(
        ModelType.XGBOOST,
        early_stopping_rounds=2,
        n_estimators=20,
    )
    splitter = DataSplitter(n_splits=2)
    matrix_builder = TemporalMatrixBuilder(
        cleaning_config=HistoryCleanerConfig(winsorized_quantile=1.0)
    )

    tree_count = trainer.select_final_tree_count(
        dummy_raw_data,
        splitter,
        matrix_builder,
    )

    assert 1 <= tree_count <= trainer.n_estimators


def test_fit_final_trains_exportable_xgboost_components(
    dummy_pipeline_data: pd.DataFrame,
) -> None:
    trainer = ModelTrainer(
        ModelType.XGBOOST,
        n_estimators=3,
    )

    result = trainer.fit_final(dummy_pipeline_data)

    assert result is trainer
    assert isinstance(trainer.model, XGBRegressor)
    assert trainer.preprocessor is not None
    assert trainer.model.get_params()["n_estimators"] == 3


def test_fit_final_trains_exportable_linear_components(
    dummy_pipeline_data: pd.DataFrame,
) -> None:
    trainer = ModelTrainer(ModelType.LOG_LIN)

    result = trainer.fit_final(dummy_pipeline_data)

    assert result is trainer
    assert isinstance(trainer.model, Ridge)
    assert trainer.preprocessor is not None
