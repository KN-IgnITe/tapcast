import numpy as np
import pandas as pd
import pytest
from ml_common.model.feature_schema import FeatureSchema
from sklearn.linear_model import Ridge
from training.data.columns import PipelineKey
from training.data.mock_data_generator import ArticleKey, DayKey, WeatherKey
from training.models.model_trainer import ModelTrainer
from training.models.ridge_strategy import RidgeTrainingStrategy
from training.models.xgboost_strategy import XGBoostTrainingStrategy
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


def test_fit_trains_exportable_xgboost_components(
    dummy_pipeline_data: pd.DataFrame,
    feature_schema: FeatureSchema,
) -> None:
    strategy = XGBoostTrainingStrategy(
        n_estimators=3,
        schema=feature_schema,
    )
    trainer = ModelTrainer(strategy=strategy)

    result = trainer.fit(dummy_pipeline_data)

    assert result is trainer
    assert isinstance(trainer.model, XGBRegressor)
    assert trainer.model.get_params()["n_estimators"] == 3
    assert trainer.preprocessor.schema == feature_schema


def test_fit_trains_exportable_linear_components(
    dummy_pipeline_data: pd.DataFrame,
    feature_schema: FeatureSchema,
) -> None:
    strategy = RidgeTrainingStrategy(schema=feature_schema)
    trainer = ModelTrainer(strategy=strategy)

    result = trainer.fit(dummy_pipeline_data)

    assert result is trainer
    assert isinstance(trainer.model, Ridge)
    assert trainer.preprocessor.schema == feature_schema


def test_predict_accepts_data_without_target(
    dummy_pipeline_data: pd.DataFrame,
    feature_schema: FeatureSchema,
) -> None:
    strategy = XGBoostTrainingStrategy(
        n_estimators=3,
        schema=feature_schema,
    )
    trainer = ModelTrainer(strategy=strategy)
    split_date = pd.Timestamp("2023-01-16")
    train_df = dummy_pipeline_data[dummy_pipeline_data[DayKey.DATE.value] < split_date]
    test_df = dummy_pipeline_data[dummy_pipeline_data[DayKey.DATE.value] >= split_date]
    features = test_df.drop(columns=[PipelineKey.TARGET_DEMAND.value])

    trainer.fit(train_df)
    predictions = trainer.predict(features)

    assert predictions.shape == (len(test_df),)
    assert np.isfinite(predictions).all()
    assert (predictions >= 0).all()
    np.testing.assert_allclose(predictions, trainer.predict(test_df))


def test_unfitted_trainer_rejects_access_and_prediction(
    dummy_pipeline_data: pd.DataFrame,
    feature_schema: FeatureSchema,
) -> None:
    trainer = ModelTrainer(RidgeTrainingStrategy(schema=feature_schema))

    with pytest.raises(RuntimeError, match="not been fitted"):
        _ = trainer.model

    with pytest.raises(RuntimeError, match="not been fitted"):
        _ = trainer.preprocessor

    with pytest.raises(RuntimeError, match="not been fitted"):
        trainer.predict(dummy_pipeline_data)


def test_fit_requires_target(
    dummy_pipeline_data: pd.DataFrame,
    feature_schema: FeatureSchema,
) -> None:
    trainer = ModelTrainer(RidgeTrainingStrategy(schema=feature_schema))
    features = dummy_pipeline_data.drop(columns=[PipelineKey.TARGET_DEMAND.value])

    with pytest.raises(ValueError, match="Missing target column"):
        trainer.fit(features)


def test_fit_with_early_stopping_fits_preprocessor_only_on_train(
    dummy_pipeline_data: pd.DataFrame,
    feature_schema: FeatureSchema,
) -> None:
    train_df = dummy_pipeline_data.iloc[:30].copy()
    validation_df = dummy_pipeline_data.iloc[30:].copy()
    validation_df[ArticleKey.PLU.value] = 999
    strategy = XGBoostTrainingStrategy(
        n_estimators=20,
        early_stopping_rounds=2,
        schema=feature_schema,
    )
    trainer = ModelTrainer(strategy=strategy)

    result = trainer.fit_with_early_stopping(train_df, validation_df)
    transformed = trainer.preprocessor.transform(validation_df)

    assert result is trainer
    assert transformed[ArticleKey.PLU.value].isna().all()
    assert 0 <= trainer.model.best_iteration < 20
    assert trainer.predict(validation_df).shape == (len(validation_df),)


def test_fit_with_early_stopping_rejects_unsupported_strategy(
    dummy_pipeline_data: pd.DataFrame,
    feature_schema: FeatureSchema,
) -> None:
    trainer = ModelTrainer(RidgeTrainingStrategy(schema=feature_schema))

    with pytest.raises(TypeError, match="not support early stopping"):
        trainer.fit_with_early_stopping(
            dummy_pipeline_data.iloc[:30],
            dummy_pipeline_data.iloc[30:],
        )
