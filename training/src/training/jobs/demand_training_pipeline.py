import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from ml_common.artifacts.model_bundle_store import ModelBundleStore

from training.artifacts.model_bundle import (
    ProductionModelBundle,
    ProductionModelBundleExporter,
)
from training.artifacts.xgboost_io import XGBoostExporter
from training.data.data_loader import DemandDataLoader
from training.data.data_splitter import DataSplitter
from training.data.sql_to_json_exporter import SQLToJSONExporter
from training.evaluation.backtest import BacktestResult, BackTestRunner
from training.evaluation.baseline import Lag14Baseline
from training.evaluation.model_comparison import ModelComparison
from training.evaluation.window_evaluator import WindowEvaluator
from training.features.history_cleaner import HistoryCleanerConfig
from training.features.temporal_matrix_builder import TemporalMatrixBuilder
from training.jobs.training_job_repository import ClaimedTrainingJob
from training.jobs.training_job_runner import TrainingPipeline
from training.models.model_trainer import (
    ModelTrainer,
    ModelType,
    XGBoostObjective,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SelectedModelConfiguration:
    """Configuration selected during model evaluation."""

    objective: XGBoostObjective
    tree_count: int
    early_stopping_rounds: int


class DemandTrainingPipeline(TrainingPipeline):
    """Train and export a production demand model for one job."""

    def __init__(
        self,
        data_exporter: SQLToJSONExporter,
        model_bundle_store: ModelBundleStore,
        artifact_root: Path,
        cleaning_config: HistoryCleanerConfig,
    ) -> None:
        self._data_exporter = data_exporter
        self._model_bundle_store = model_bundle_store
        self._artifact_root = artifact_root
        self._cleaning_config = cleaning_config

    def run(self, job: ClaimedTrainingJob) -> str:
        """Execute training and return the uploaded bundle prefix."""

        logger.info(
            "Starting demand training: job_id=%s, bar_id=%s",
            job.job_id,
            job.bar_id,
        )

        raw_df = self._load_data(job.bar_id)

        splitter = DataSplitter(
            test_size=0.15,
            n_splits=5,
        )
        matrix_builder = TemporalMatrixBuilder(
            cleaning_config=self._cleaning_config,
        )

        raw_train_val, raw_test = splitter.get_final_test_split(raw_df)

        configuration, backtest = self._select_configuration(
            raw_train_val,
            splitter,
            matrix_builder,
        )

        baseline_metrics = self._calculate_baseline(
            raw_train_val,
            splitter,
            matrix_builder,
        )

        test_metrics = self._evaluate_on_final_test(
            raw_train_val,
            raw_test,
            matrix_builder,
            configuration,
        )

        self._log_evaluation(
            configuration,
            backtest,
            baseline_metrics,
            test_metrics,
        )

        prefix = self._resolve_bundle_prefix(job)

        self._fit_export_and_upload(
            job=job,
            raw_df=raw_df,
            matrix_builder=matrix_builder,
            configuration=configuration,
            prefix=prefix,
        )

        logger.info(
            "Demand training completed: job_id=%s, prefix=%s",
            job.job_id,
            prefix,
        )

        return prefix

    def _load_data(self, bar_id: int) -> pd.DataFrame:
        """Export bar data from PostgreSQL and load it as a DataFrame."""

        self._data_exporter.export(bar_id)

        loader = DemandDataLoader(
            file_path=self._data_exporter.paths.output_path,
            contract_path=self._data_exporter.paths.contract_path,
        )

        return loader.load_and_process()

    def _select_configuration(
        self,
        raw_train_val: pd.DataFrame,
        splitter: DataSplitter,
        matrix_builder: TemporalMatrixBuilder,
    ) -> tuple[SelectedModelConfiguration, BacktestResult]:
        """Select objective and final tree count using training data."""

        comparison = ModelComparison.compare_objectives(
            raw_train_val,
            splitter,
            matrix_builder,
        )

        objective = ModelComparison.select_best_objective(
            comparison,
            metric="WAPE",
        )

        trainer = ModelTrainer(
            model_type=ModelType.XGBOOST,
            xgboost_objective=objective,
        )

        backtest = trainer.run_walk_forward_training(
            raw_train_val,
            splitter,
            matrix_builder,
        )

        tree_count = trainer.select_final_tree_count(
            raw_train_val,
            splitter,
            matrix_builder,
        )

        configuration = SelectedModelConfiguration(
            objective=objective,
            tree_count=tree_count,
            early_stopping_rounds=trainer.early_stopping_rounds,
        )

        return configuration, backtest

    @staticmethod
    def _calculate_baseline(
        raw_train_val: pd.DataFrame,
        splitter: DataSplitter,
        matrix_builder: TemporalMatrixBuilder,
    ) -> dict[str, float]:
        """Calculate average Lag-14 baseline metrics."""

        folds = BackTestRunner(splitter).run_raw(
            raw_train_val,
            Lag14Baseline(),
            matrix_builder,
        )

        if not folds:
            raise RuntimeError("Baseline backtest produced no folds.")

        return {
            metric: float(np.mean([fold[metric] for fold in folds]))
            for metric in folds[0]
        }

    @staticmethod
    def _evaluate_on_final_test(
        raw_train_val: pd.DataFrame,
        raw_test: pd.DataFrame,
        matrix_builder: TemporalMatrixBuilder,
        configuration: SelectedModelConfiguration,
    ) -> dict[str, float]:
        """Evaluate the selected configuration on untouched test data."""

        train_val_matrix, test_matrix = matrix_builder.build_train_evaluation(
            raw_train_val,
            raw_test,
        )

        trainer = ModelTrainer(
            model_type=ModelType.XGBOOST,
            xgboost_objective=configuration.objective,
            n_estimators=configuration.tree_count,
        )

        return trainer.evaluate_on_test(
            train_val_matrix,
            test_matrix,
        )

    def _fit_export_and_upload(
        self,
        job: ClaimedTrainingJob,
        raw_df: pd.DataFrame,
        matrix_builder: TemporalMatrixBuilder,
        configuration: SelectedModelConfiguration,
        prefix: str,
    ) -> None:
        """Train the production model and upload its bundle."""

        final_matrix, final_cleaner = matrix_builder.build_training(raw_df)

        trainer = ModelTrainer(
            model_type=ModelType.XGBOOST,
            xgboost_objective=configuration.objective,
            n_estimators=configuration.tree_count,
        )
        trainer.fit_final(final_matrix)

        if trainer.model is None:
            raise RuntimeError("Production model was not fitted.")

        if trainer.preprocessor is None:
            raise RuntimeError("Production preprocessor was not fitted.")

        artifact_dir = self._artifact_root / str(job.job_id)

        bundle = ProductionModelBundle(
            model=trainer.model,
            preprocessor=trainer.preprocessor,
            cleaner=final_cleaner,
            metadata={
                "job_id": str(job.job_id),
                "bar_id": job.bar_id,
                "model_type": ModelType.XGBOOST.value,
                "xgboost_objective": configuration.objective,
                "n_estimators": configuration.tree_count,
                "early_stopping_rounds": (configuration.early_stopping_rounds),
                "scale_numeric": trainer.scale_numeric,
                "cleaning_config": {
                    "winsorized_quantile": (self._cleaning_config.winsorized_quantile),
                    "min_winsorization_observations": (
                        self._cleaning_config.min_winsorization_observations
                    ),
                    "enable_winsorization": (
                        self._cleaning_config.enable_winsorization
                    ),
                    "enable_oos_imputation": (
                        self._cleaning_config.enable_oos_imputation
                    ),
                },
            },
        )

        ProductionModelBundleExporter(
            model_exporter=XGBoostExporter(),
            model_filename="xgb_model.json",
        ).save(
            bundle,
            artifact_dir,
        )

        self._model_bundle_store.upload_bundle_from_dir(
            source_dir=artifact_dir,
            prefix=prefix,
        )

    @staticmethod
    def _log_evaluation(
        configuration: SelectedModelConfiguration,
        backtest: BacktestResult,
        baseline_metrics: dict[str, float],
        test_metrics: dict[str, float],
    ) -> None:
        """Log model selection and evaluation results."""

        logger.info(
            "Selected model: objective=%s, tree_count=%s",
            configuration.objective,
            configuration.tree_count,
        )
        logger.info(
            "XGBoost backtest metrics: %s",
            backtest.global_metrics,
        )
        logger.info(
            "Lag-14 baseline metrics: %s",
            baseline_metrics,
        )
        logger.info(
            "Final untouched test metrics: %s",
            test_metrics,
        )

        for window_days in (1, 7, 14):
            result = WindowEvaluator.evaluate(
                backtest.predictions,
                window_days,
            )
            logger.info(
                "%s-day window backtest metrics: %s",
                window_days,
                result.metrics,
            )

    @classmethod
    def _resolve_bundle_prefix(
        cls,
        job: ClaimedTrainingJob,
    ) -> str:
        """Use the stored bundle prefix or generate one."""

        if job.model_bundle_prefix:
            return job.model_bundle_prefix

        return cls._build_bundle_prefix(job)

    @staticmethod
    def _build_bundle_prefix(job: ClaimedTrainingJob) -> str:
        """Build a deterministic S3 prefix for a training job."""

        return f"models/bars/{job.bar_id}/jobs/{job.job_id}"
