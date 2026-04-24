import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import Ridge
from training.data.data_splitter import DataSplitter
from training.data.mock_data_generator import ArticleKey, DayKey, WeatherKey
from training.models.model_trainer import ModelTrainer, ModelType
from xgboost import XGBRegressor


@pytest.fixture
def dummy_pipeline_data() -> pd.DataFrame:
    """Fixture to create dummy data for testing the entire pipeline."""

    np.random.seed(42)
    dates = pd.date_range(start="2023-01-01", periods=20)

    return pd.DataFrame(
        {
            WeatherKey.AVG_TEMP.value: np.random.rand(20) * 20,
            WeatherKey.TEMP_AMPLITUDE.value: np.random.rand(20) * 5,
            WeatherKey.RAIN.value: np.zeros(20),
            ArticleKey.YESTERDAY_DEMAND.value: np.random.randint(10, 50, 20),
            ArticleKey.WEEK_AGO_DEMAND.value: np.random.randint(10, 50, 20),
            DayKey.DAY_OF_WEEK.value: np.random.randint(1, 8, 20),
            ArticleKey.CATEGORY.value: [1, 2] * 10,
            ArticleKey.PLU.value: [101, 102] * 10,
            ArticleKey.DEMAND.value: np.random.randint(10, 100, 20),
            DayKey.DATE.value: dates,
        }
    )


def test_get_model_returns_correct_instances() -> None:
    """Checks if factory method returns correct model"""
    trainer_log = ModelTrainer(ModelType.LOG_LIN)

    assert isinstance(trainer_log._get_model(), Ridge)

    trainer_xgb = ModelTrainer(ModelType.XGBOOST)
    assert isinstance(trainer_xgb._get_model(), XGBRegressor)


def test_calculate_metrics_returns_expected_results() -> None:
    """Checks if metrics are calculated correctly"""
    trainer = ModelTrainer(ModelType.LOG_LIN)

    y_true: pd.Series[int] = pd.Series([10, 20, 30])
    y_pred: pd.Series[float] = pd.Series([12.0, 18.0, 30.0])

    metrics = trainer._calculate_metrics(y_true, y_pred)

    assert "MAE" in metrics
    assert "MAPE" in metrics

    assert np.isclose(metrics["MAE"], 4 / 3)

    assert np.isclose(metrics["MAPE"], 4 / 60)


def test_run_walk_forward_training_executes_succesfully(
    dummy_pipeline_data: pd.DataFrame,
) -> None:
    """Checks if the entire pipeline runs without errors and returns metrics"""
    trainer = ModelTrainer(ModelType.LOG_LIN)
    splitter = DataSplitter(n_splits=2)

    avg_mae = trainer.run_walk_forward_training(dummy_pipeline_data, splitter)

    assert isinstance(avg_mae, float)
    assert avg_mae >= 0.0


def test_evaluate_on_test_executes_succesfully(
    dummy_pipeline_data: pd.DataFrame,
) -> None:
    """Checks final evaluation on test with xgboost model"""
    trainer = ModelTrainer(ModelType.XGBOOST)

    train_df = dummy_pipeline_data.iloc[:15]
    test_df = dummy_pipeline_data.iloc[15:]

    mae = trainer.evaluate_on_test(train_df, test_df)

    assert isinstance(mae, float)
    assert mae >= 0.0
