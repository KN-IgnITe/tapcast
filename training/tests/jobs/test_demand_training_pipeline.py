from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

import training.jobs.demand_training_pipeline as pipeline_module
from ml_common.artifacts.model_bundle_store import ModelBundleStore
from training.data.sql_to_json_exporter import ExporterPaths, SQLToJSONExporter
from training.evaluation.backtest import BacktestResult
from training.features.history_cleaner import HistoryCleanerConfig
from training.jobs.demand_training_pipeline import (
    DemandTrainingPipeline,
    SelectedModelConfiguration,
)
from training.jobs.training_job_repository import ClaimedTrainingJob


@pytest.fixture
def data_exporter(tmp_path: Path) -> MagicMock:
    exporter = MagicMock(spec=SQLToJSONExporter)
    exporter.paths = ExporterPaths(
        query_path=tmp_path / "query.sql",
        contract_path=tmp_path / "contract.json",
        output_path=tmp_path / "sql_export.json",
    )
    return exporter


@pytest.fixture
def model_bundle_store() -> MagicMock:
    return MagicMock(spec=ModelBundleStore)


@pytest.fixture
def cleaning_config() -> HistoryCleanerConfig:
    return HistoryCleanerConfig(
        winsorized_quantile=0.99,
        min_winsorization_observations=20,
        enable_winsorization=True,
        enable_oos_imputation=False,
    )


@pytest.fixture
def demand_pipeline(
    data_exporter: MagicMock,
    model_bundle_store: MagicMock,
    tmp_path: Path,
    cleaning_config: HistoryCleanerConfig,
) -> DemandTrainingPipeline:
    return DemandTrainingPipeline(
        data_exporter=data_exporter,
        model_bundle_store=model_bundle_store,
        artifact_root=tmp_path / "artifacts",
        cleaning_config=cleaning_config,
    )


def test_run_executes_training_flow_and_returns_bundle_prefix(
    demand_pipeline: DemandTrainingPipeline,
    claimed_job: ClaimedTrainingJob,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_df = pd.DataFrame({"value": [1, 2, 3]})
    raw_train_val = raw_df.iloc[:2]
    raw_test = raw_df.iloc[2:]

    splitter = MagicMock()
    splitter.get_final_test_split.return_value = (raw_train_val, raw_test)
    matrix_builder = MagicMock()

    splitter_factory = MagicMock(return_value=splitter)
    matrix_builder_factory = MagicMock(return_value=matrix_builder)
    monkeypatch.setattr(pipeline_module, "DataSplitter", splitter_factory)
    monkeypatch.setattr(
        pipeline_module,
        "TemporalMatrixBuilder",
        matrix_builder_factory,
    )

    configuration = SelectedModelConfiguration(
        objective="count:poisson",
        tree_count=120,
        early_stopping_rounds=30,
    )
    backtest = MagicMock(spec=BacktestResult)

    load_data = MagicMock(return_value=raw_df)
    select_configuration = MagicMock(return_value=(configuration, backtest))
    calculate_baseline = MagicMock(return_value={"WAPE": 0.4})
    evaluate_final_test = MagicMock(return_value={"WAPE": 0.42})
    log_evaluation = MagicMock()
    fit_export_upload = MagicMock()

    monkeypatch.setattr(demand_pipeline, "_load_data", load_data)
    monkeypatch.setattr(
        demand_pipeline,
        "_select_configuration",
        select_configuration,
    )
    monkeypatch.setattr(
        demand_pipeline,
        "_calculate_baseline",
        calculate_baseline,
    )
    monkeypatch.setattr(
        demand_pipeline,
        "_evaluate_on_final_test",
        evaluate_final_test,
    )
    monkeypatch.setattr(
        demand_pipeline,
        "_log_evaluation",
        log_evaluation,
    )
    monkeypatch.setattr(
        demand_pipeline,
        "_fit_export_and_upload",
        fit_export_upload,
    )

    result = demand_pipeline.run(claimed_job)

    expected_prefix = f"models/bars/{claimed_job.bar_id}/jobs/{claimed_job.job_id}"
    assert result == expected_prefix
    load_data.assert_called_once_with(claimed_job.bar_id)
    select_configuration.assert_called_once_with(
        raw_train_val,
        splitter,
        matrix_builder,
    )
    calculate_baseline.assert_called_once_with(
        raw_train_val,
        splitter,
        matrix_builder,
    )
    evaluate_final_test.assert_called_once_with(
        raw_train_val,
        raw_test,
        matrix_builder,
        configuration,
    )
    log_evaluation.assert_called_once_with(
        configuration,
        backtest,
        {"WAPE": 0.4},
        {"WAPE": 0.42},
    )

    upload_call = fit_export_upload.call_args.kwargs
    assert upload_call["job"] == claimed_job
    assert upload_call["raw_df"] is raw_df
    assert upload_call["matrix_builder"] is matrix_builder
    assert upload_call["configuration"] == configuration
    assert upload_call["prefix"] == expected_prefix


def test_resolve_bundle_prefix_uses_prefix_from_job(
    claimed_job: ClaimedTrainingJob,
) -> None:
    job = ClaimedTrainingJob(
        **{
            **claimed_job.__dict__,
            "model_bundle_prefix": "models/custom/model",
        }
    )

    result = DemandTrainingPipeline._resolve_bundle_prefix(job)

    assert result == "models/custom/model"


def test_resolve_bundle_prefix_generates_prefix_when_missing(
    claimed_job: ClaimedTrainingJob,
) -> None:
    result = DemandTrainingPipeline._resolve_bundle_prefix(claimed_job)

    assert result == (f"models/bars/{claimed_job.bar_id}/jobs/{claimed_job.job_id}")


def test_calculate_baseline_averages_fold_metrics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backtest_runner = MagicMock()
    backtest_runner.run_raw.return_value = [
        {"MAE": 2.0, "WAPE": 0.4},
        {"MAE": 4.0, "WAPE": 0.6},
    ]
    monkeypatch.setattr(
        pipeline_module,
        "BackTestRunner",
        MagicMock(return_value=backtest_runner),
    )

    result = DemandTrainingPipeline._calculate_baseline(
        MagicMock(),
        MagicMock(),
        MagicMock(),
    )

    assert result == {"MAE": 3.0, "WAPE": 0.5}


def test_calculate_baseline_rejects_empty_backtest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backtest_runner = MagicMock()
    backtest_runner.run_raw.return_value = []
    monkeypatch.setattr(
        pipeline_module,
        "BackTestRunner",
        MagicMock(return_value=backtest_runner),
    )

    with pytest.raises(
        RuntimeError,
        match="Baseline backtest produced no folds",
    ):
        DemandTrainingPipeline._calculate_baseline(
            MagicMock(),
            MagicMock(),
            MagicMock(),
        )


def test_load_data_exports_bar_before_loading_json(
    demand_pipeline: DemandTrainingPipeline,
    data_exporter: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = pd.DataFrame({"value": [1, 2]})
    loader = MagicMock()
    loader.load_and_process.return_value = expected
    loader_factory = MagicMock(return_value=loader)
    monkeypatch.setattr(
        pipeline_module,
        "DemandDataLoader",
        loader_factory,
    )

    result = demand_pipeline._load_data(17)

    data_exporter.export.assert_called_once_with(17)
    loader_factory.assert_called_once_with(
        file_path=data_exporter.paths.output_path,
        contract_path=data_exporter.paths.contract_path,
    )
    assert result is expected
