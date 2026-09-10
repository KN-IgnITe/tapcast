from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest
from ml_common.model.feature_schema import FeatureSchema
from ml_common.model.model_kind import ModelKind
from ml_common.model.preprocessing import XGBoostPreprocessor
from training.artifacts.json_io import JsonExporter
from training.artifacts.model_bundle import (
    ProductionModelBundle,
    ProductionModelBundleExporter,
    ProductionModelBundleImporter,
)
from training.artifacts.xgboost_io import XGBoostExporter, XGBoostImporter
from training.data.columns import PipelineKey
from training.data.mock_data_generator import ArticleKey, DayKey, WeatherKey
from training.features.history_cleaner import HistoryCleaner, HistoryCleanerConfig
from xgboost import XGBRegressor


def _training_matrix() -> pd.DataFrame:
    return pd.DataFrame(
        {
            DayKey.DATE.value: pd.to_datetime(
                ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"]
            ),
            ArticleKey.PLU.value: [101, 102, 101, 102],
            ArticleKey.CATEGORY.value: [1, 2, 1, 2],
            WeatherKey.AVG_TEMP.value: [10.0, 12.0, 14.0, 16.0],
            PipelineKey.DEMAND_LAG_14D.value: [8.0, 10.0, 12.0, 14.0],
            PipelineKey.TARGET_DEMAND.value: [10.0, 13.0, 16.0, 19.0],
        }
    )


def _fitted_cleaner(raw_history_row_factory: Any) -> HistoryCleaner:
    cleaner = HistoryCleaner(
        config=HistoryCleanerConfig(
            winsorized_quantile=1.0,
            min_winsorization_observations=1,
        )
    )
    cleaner.fit(
        pd.DataFrame(
            [
                raw_history_row_factory("2026-01-01", 101, 1, 10),
                raw_history_row_factory("2026-01-02", 101, 1, 12),
                raw_history_row_factory("2026-01-03", 102, 2, 8),
            ]
        )
    )
    return cleaner


def test_production_model_bundle_exporter_writes_expected_files(
    tmp_path: Path,
    raw_history_row_factory: Any,
    feature_schema: FeatureSchema,
) -> None:
    train_df = _training_matrix()
    preprocessor = XGBoostPreprocessor(schema=feature_schema)
    X_train = preprocessor.fit_transform(train_df)
    y_train = train_df[PipelineKey.TARGET_DEMAND.value]
    model = XGBRegressor(
        n_estimators=3,
        max_depth=2,
        enable_categorical=True,
        tree_method="hist",
        objective="reg:squarederror",
        random_state=42,
    )
    model.fit(X_train, y_train)

    bundle = ProductionModelBundle(
        model=model,
        model_kind=ModelKind.XGBOOST,
        preprocessor=preprocessor,
        cleaner=_fitted_cleaner(raw_history_row_factory),
        metadata={"schema_version": 1, "objective": "reg:squarederror"},
    )

    ProductionModelBundleExporter(
        model_exporter=XGBoostExporter(),
        model_filename="xgb_model.json",
    ).save(bundle, tmp_path)

    assert (tmp_path / "xgb_model.json").exists()
    assert (tmp_path / "preprocessor.joblib").exists()
    assert (tmp_path / "cleaner_artifacts.json").exists()
    assert (tmp_path / "metadata.json").exists()


def test_production_model_bundle_importer_restores_prediction_parity(
    tmp_path: Path,
    raw_history_row_factory: Any,
    feature_schema: FeatureSchema,
) -> None:
    train_df = _training_matrix()
    preprocessor = XGBoostPreprocessor(schema=feature_schema)
    X_train = preprocessor.fit_transform(train_df)
    y_train = train_df[PipelineKey.TARGET_DEMAND.value]
    model = XGBRegressor(
        n_estimators=3,
        max_depth=2,
        enable_categorical=True,
        tree_method="hist",
        objective="reg:squarederror",
        random_state=42,
    )
    model.fit(X_train, y_train)

    bundle = ProductionModelBundle(
        model=model,
        model_kind=ModelKind.XGBOOST,
        preprocessor=preprocessor,
        cleaner=_fitted_cleaner(raw_history_row_factory),
        metadata={"schema_version": 1, "objective": "reg:squarederror"},
    )
    exporter = ProductionModelBundleExporter(
        model_exporter=XGBoostExporter(),
        model_filename="xgb_model.json",
    )
    exporter.save(bundle, tmp_path)

    loaded_bundle = ProductionModelBundleImporter(
        model_importer=XGBoostImporter(),
    ).load(tmp_path)

    X_before = preprocessor.transform(train_df)
    X_after = loaded_bundle.preprocessor.transform(train_df)

    pd.testing.assert_frame_equal(X_after, X_before)

    np.testing.assert_allclose(
        loaded_bundle.model.predict(X_after),
        model.predict(X_before),
    )
    assert loaded_bundle.model_kind == ModelKind.XGBOOST
    assert loaded_bundle.preprocessor.schema == feature_schema
    assert loaded_bundle.cleaner.is_fitted
    assert loaded_bundle.metadata["model_file"] == "xgb_model.json"


def test_production_model_bundle_importer_rejects_missing_model_filename(
    tmp_path: Path,
) -> None:
    JsonExporter().save({"schema_version": 1}, tmp_path / "metadata.json")

    importer = ProductionModelBundleImporter(
        model_importer=XGBoostImporter(),
    )

    with pytest.raises(ValueError, match="model_file"):
        importer.load(tmp_path)
