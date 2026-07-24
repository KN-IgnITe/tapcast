import os
from pathlib import Path

import numpy as np

from ml_common.artifacts.s3_model_bundle_store import S3ModelBundleStore
from ml_common.storage.s3_client import S3Client
from ml_common.storage.s3_config import S3Config
from training.data.data_loader import DemandDataLoader
from training.data.data_splitter import DataSplitter
from training.artifacts.model_bundle import (
    ProductionModelBundle,
    ProductionModelBundleExporter,
)
from training.artifacts.xgboost_io import XGBoostExporter
from training.evaluation.backtest import BackTestRunner
from training.evaluation.baseline import Lag14Baseline
from training.evaluation.model_comparison import ModelComparison
from training.evaluation.window_evaluator import WindowEvaluator
from training.features.history_cleaner import HistoryCleanerConfig
from training.features.temporal_matrix_builder import TemporalMatrixBuilder
from training.models.model_trainer import ModelTrainer, ModelType


DEFAULT_MODEL_BUNDLE_S3_PREFIX = "demand-model/latest"


def main() -> None:
    project_dir = Path(__file__).parents[2]
    data_path = project_dir / "data" / "raw" / "sql_export.json"
    contract_path = Path(__file__).parent / "data" / "contract.json"

    loader = DemandDataLoader(data_path, contract_path)
    splitter = DataSplitter(test_size=0.15, n_splits=5)

    cleaning_config = HistoryCleanerConfig(
        winsorized_quantile=0.99,
        min_winsorization_observations=20,
        enable_winsorization=True,
        enable_oos_imputation=False,
    )

    matrix_builder = TemporalMatrixBuilder(
        cleaning_config=cleaning_config,
    )

    raw_df = loader.load_and_process()

    raw_train_val_df, raw_test_df = splitter.get_final_test_split(raw_df)

    comparison = ModelComparison.compare_objectives(
        raw_train_val_df,
        splitter,
        matrix_builder,
    )

    print("\nObjective comparison:")
    print(comparison.to_string(index=False))

    best_objective = ModelComparison.select_best_objective(
        comparison,
        metric="WAPE",
    )

    print(f"\nSelected objective: {best_objective}")

    trainer = ModelTrainer(
        model_type=ModelType.XGBOOST,
        xgboost_objective=best_objective,
    )
    # trainer = ModelTrainer(
    #     model_type=ModelType.LOG_LIN
    # )

    backtest_result = trainer.run_walk_forward_training(
        raw_train_val_df,
        splitter,
        matrix_builder,
    )

    final_tree_count = trainer.select_final_tree_count(
        raw_train_val_df,
        splitter,
        matrix_builder,
    )

    print(f"\nFinal tree count: {final_tree_count}")

    baseline_folds = BackTestRunner(splitter).run_raw(
        raw_train_val_df,
        Lag14Baseline(),
        matrix_builder,
    )

    baseline_metrics = {
        metric: float(np.mean([fold[metric] for fold in baseline_folds]))
        for metric in baseline_folds[0]
    }

    print("\nXGBoost backtest:")
    print(backtest_result.global_metrics)

    print("\nLag-14 baseline:")
    print(baseline_metrics)

    print("\nPer category:")
    print(backtest_result.per_category.to_string(index=False))

    print("\nPer PLU:")
    print(backtest_result.per_plu.to_string(index=False))

    for window_days in (1, 7, 14):
        window_result = WindowEvaluator.evaluate(
            backtest_result.predictions,
            window_days,
        )
        print(f"\n{window_days}-day window backtest:")
        print(window_result.metrics)

    train_val_matrix, test_matrix = matrix_builder.build_train_evaluation(
        raw_train_val_df,
        raw_test_df,
    )

    evaluation_trainer = ModelTrainer(
        model_type=ModelType.XGBOOST,
        xgboost_objective=best_objective,
        n_estimators=final_tree_count,
    )
    test_metrics = evaluation_trainer.evaluate_on_test(
        train_val_matrix,
        test_matrix,
    )

    print("\nFinal untouched test:")
    print(test_metrics)

    final_matrix, final_cleaner = matrix_builder.build_training(raw_df)

    production_trainer = ModelTrainer(
        model_type=ModelType.XGBOOST,
        xgboost_objective=best_objective,
        n_estimators=final_tree_count,
    )
    production_trainer.fit_final(final_matrix)

    production_model = production_trainer.model
    production_preprocessor = production_trainer.preprocessor

    if production_model is None:
        raise RuntimeError("Production model was not fitted.")

    if production_preprocessor is None:
        raise RuntimeError("Production preprocessor was not fitted.")

    artifact_dir = project_dir / "artifacts" / "production"
    production_bundle = ProductionModelBundle(
        model=production_model,
        preprocessor=production_preprocessor,
        cleaner=final_cleaner,
        metadata={
            "model_type": ModelType.XGBOOST.value,
            "xgboost_objective": best_objective,
            "n_estimators": final_tree_count,
            "early_stopping_rounds": trainer.early_stopping_rounds,
            "scale_numeric": production_trainer.scale_numeric,
            "source_data": str(data_path.relative_to(project_dir)),
            "cleaning_config": {
                "winsorized_quantile": cleaning_config.winsorized_quantile,
                "min_winsorization_observations": (
                    cleaning_config.min_winsorization_observations
                ),
                "enable_winsorization": cleaning_config.enable_winsorization,
                "enable_oos_imputation": cleaning_config.enable_oos_imputation,
            },
        },
    )

    ProductionModelBundleExporter(
        model_exporter=XGBoostExporter(),
        model_filename="xgb_model.json",
    ).save(
        production_bundle,
        artifact_dir,
    )

    model_bundle_s3_prefix = os.getenv(
        "MODEL_BUNDLE_S3_PREFIX",
        DEFAULT_MODEL_BUNDLE_S3_PREFIX,
    )
    _upload_production_bundle_to_s3(
        artifact_dir=artifact_dir,
        prefix=model_bundle_s3_prefix,
    )

    print("\nProduction artifacts ready:")
    print(f"Artifact directory: {artifact_dir}")
    print(f"S3 prefix: {model_bundle_s3_prefix}")
    print(f"Model trees: {final_tree_count}")
    print(
        "Winsorization thresholds: "
        f"{len(final_cleaner.artifacts_winsorization_threshold)}"
    )


def _upload_production_bundle_to_s3(artifact_dir: Path, prefix: str) -> None:
    """Upload production model bundle to S3-compatible storage."""

    s3_config = S3Config()

    with S3Client(s3_config) as s3_client:
        s3_client.ensure_bucket_exists()

        S3ModelBundleStore(s3_client).upload_bundle_from_dir(
            source_dir=artifact_dir,
            prefix=prefix,
        )


if __name__ == "__main__":
    main()
