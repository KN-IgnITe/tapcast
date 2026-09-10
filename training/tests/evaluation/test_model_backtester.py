from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest
from training.data.columns import PipelineKey
from training.data.data_splitter import DataSplitter
from training.data.mock_data_generator import ArticleKey, DayKey
from training.evaluation import model_backtester as backtester_module
from training.evaluation.backtest import BacktestResult
from training.evaluation.model_backtester import ModelBacktester
from training.features.history_cleaner import HistoryCleanerConfig
from training.features.temporal_matrix_builder import TemporalMatrixBuilder
from training.models.model_trainer import ModelTrainer
from training.models.training_strategy import ModelTrainingStrategy
from training.models.xgboost_strategy import XGBoostTrainingStrategy


def _as_matrix(raw: pd.DataFrame) -> pd.DataFrame:
    return raw.rename(
        columns={ArticleKey.DEMAND.value: PipelineKey.TARGET_DEMAND.value}
    ).copy()


@pytest.fixture
def raw_history() -> pd.DataFrame:
    return pd.DataFrame(
        {
            DayKey.DATE.value: pd.date_range("2026-01-01", periods=8),
            ArticleKey.PLU.value: [101, 102] * 4,
            ArticleKey.CATEGORY.value: [1, 2] * 4,
            ArticleKey.DEMAND.value: [1.0, 2.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
        },
        index=[10, 20, 30, 40, 50, 60, 70, 80],
    )


@pytest.fixture
def strategy() -> MagicMock:
    mock = MagicMock(spec=ModelTrainingStrategy)
    mock.uses_early_stopping = False
    return mock


@pytest.fixture
def splitter() -> MagicMock:
    def split_inner(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        midpoint = len(raw) // 2
        return raw.iloc[:midpoint].copy(), raw.iloc[midpoint:].copy()

    mock = MagicMock(spec=DataSplitter)
    mock.get_walk_forward_splits.return_value = [
        (np.array([0, 1]), np.array([2, 3])),
        (np.array([0, 1, 2, 3]), np.array([4, 5, 6, 7])),
    ]
    mock.get_inner_validation_split.side_effect = split_inner
    return mock


@pytest.fixture
def matrix_builder() -> MagicMock:
    mock = MagicMock(spec=TemporalMatrixBuilder)
    mock.build_train_evaluation.side_effect = lambda raw_train, raw_evaluation: (
        _as_matrix(raw_train),
        _as_matrix(raw_evaluation),
    )
    mock.build_early_stopping_fold.side_effect = (
        lambda raw_inner_train, raw_early_stop, raw_outer_validation: (
            _as_matrix(raw_inner_train),
            _as_matrix(raw_early_stop),
            _as_matrix(raw_outer_validation),
        )
    )
    return mock


@pytest.fixture
def trainers() -> tuple[MagicMock, MagicMock]:
    first = MagicMock(spec=ModelTrainer)
    first.predict.return_value = np.array([8.0, 22.0])
    second = MagicMock(spec=ModelTrainer)
    second.predict.return_value = np.array([20.0, 35.0, 60.0, 55.0])
    return first, second


@pytest.fixture
def trainer_factory(
    monkeypatch: pytest.MonkeyPatch,
    trainers: tuple[MagicMock, MagicMock],
) -> MagicMock:
    factory = MagicMock(side_effect=trainers)
    monkeypatch.setattr(backtester_module, "ModelTrainer", factory)
    return factory


@pytest.fixture
def backtester(
    strategy: MagicMock,
    splitter: MagicMock,
    matrix_builder: MagicMock,
    trainer_factory: MagicMock,
) -> ModelBacktester[object]:
    return ModelBacktester(
        strategy=strategy,
        splitter=splitter,
        matrix_builder=matrix_builder,
    )


def test_standard_folds_fit_fresh_trainers_on_training_matrices(
    backtester: ModelBacktester[object],
    raw_history: pd.DataFrame,
    strategy: MagicMock,
    splitter: MagicMock,
    matrix_builder: MagicMock,
    trainer_factory: MagicMock,
    trainers: tuple[MagicMock, MagicMock],
) -> None:
    backtester.run(raw_history)

    splitter.get_walk_forward_splits.assert_called_once()
    assert splitter.get_walk_forward_splits.call_args.args[0] is raw_history
    splitter.get_inner_validation_split.assert_not_called()
    matrix_builder.build_early_stopping_fold.assert_not_called()
    assert matrix_builder.build_train_evaluation.call_count == 2
    assert trainer_factory.call_count == 2
    for call in trainer_factory.call_args_list:
        assert call.args == (strategy,)

    for trainer, (train_end, validation_end), call in zip(
        trainers,
        [(2, 4), (4, 8)],
        matrix_builder.build_train_evaluation.call_args_list,
        strict=True,
    ):
        raw_train = raw_history.iloc[:train_end]
        raw_validation = raw_history.iloc[train_end:validation_end]
        pd.testing.assert_frame_equal(call.kwargs["raw_train"], raw_train)
        pd.testing.assert_frame_equal(call.kwargs["raw_evaluation"], raw_validation)
        trainer.fit.assert_called_once()
        trainer.fit_with_early_stopping.assert_not_called()
        trainer.predict.assert_called_once()
        pd.testing.assert_frame_equal(
            trainer.fit.call_args.args[0], _as_matrix(raw_train)
        )
        pd.testing.assert_frame_equal(
            trainer.predict.call_args.args[0], _as_matrix(raw_validation)
        )


def test_early_stopping_folds_keep_outer_validation_out_of_fitting(
    backtester: ModelBacktester[object],
    raw_history: pd.DataFrame,
    strategy: MagicMock,
    splitter: MagicMock,
    matrix_builder: MagicMock,
    trainers: tuple[MagicMock, MagicMock],
) -> None:
    strategy.uses_early_stopping = True

    backtester.run(raw_history)

    matrix_builder.build_train_evaluation.assert_not_called()
    assert splitter.get_inner_validation_split.call_count == 2
    assert matrix_builder.build_early_stopping_fold.call_count == 2
    for index, (trainer, (train_end, validation_end)) in enumerate(
        zip(trainers, [(2, 4), (4, 8)], strict=True)
    ):
        midpoint = train_end // 2
        raw_inner = raw_history.iloc[:midpoint]
        raw_early_stop = raw_history.iloc[midpoint:train_end]
        raw_outer = raw_history.iloc[train_end:validation_end]
        inner_call = splitter.get_inner_validation_split.call_args_list[index]
        pd.testing.assert_frame_equal(inner_call.args[0], raw_history.iloc[:train_end])
        builder_args = matrix_builder.build_early_stopping_fold.call_args_list[
            index
        ].kwargs
        pd.testing.assert_frame_equal(builder_args["raw_inner_train"], raw_inner)
        pd.testing.assert_frame_equal(builder_args["raw_early_stop"], raw_early_stop)
        pd.testing.assert_frame_equal(builder_args["raw_outer_validation"], raw_outer)
        trainer.fit.assert_not_called()
        trainer.fit_with_early_stopping.assert_called_once()
        fit_args = trainer.fit_with_early_stopping.call_args.kwargs
        pd.testing.assert_frame_equal(fit_args["train_matrix"], _as_matrix(raw_inner))
        pd.testing.assert_frame_equal(
            fit_args["validation_matrix"], _as_matrix(raw_early_stop)
        )
        trainer.predict.assert_called_once()
        pd.testing.assert_frame_equal(
            trainer.predict.call_args.args[0], _as_matrix(raw_outer)
        )


def test_run_preserves_prediction_order_and_fold_numbers(
    backtester: ModelBacktester[object], raw_history: pd.DataFrame
) -> None:
    result = backtester.run(raw_history)

    expected = _as_matrix(raw_history.iloc[2:]).reset_index(drop=True)
    expected[PipelineKey.PREDICTION.value] = [8.0, 22.0, 20.0, 35.0, 60.0, 55.0]
    expected[PipelineKey.BACKTEST_FOLD.value] = [1, 1, 2, 2, 2, 2]
    pd.testing.assert_frame_equal(result.predictions, expected)


def test_global_metrics_use_all_predictions_not_mean_fold_metrics(
    backtester: ModelBacktester[object], raw_history: pd.DataFrame
) -> None:
    result = backtester.run(raw_history)

    assert len(result.fold_metrics) == 2
    assert result.fold_metrics[0]["MAE"] == pytest.approx(2.0)
    assert result.fold_metrics[1]["MAE"] == pytest.approx(7.5)
    assert result.fold_metrics[0]["WAPE"] == pytest.approx(4.0 / 30.0)
    assert result.fold_metrics[1]["WAPE"] == pytest.approx(30.0 / 180.0)
    assert result.global_metrics["MAE"] == pytest.approx(34.0 / 6.0)
    assert result.global_metrics["WAPE"] == pytest.approx(34.0 / 210.0)
    assert result.global_metrics["RMSE"] == pytest.approx(np.sqrt(258.0 / 6.0))
    assert result.global_metrics["R2"] == pytest.approx(1.0 - 258.0 / 1750.0)


@pytest.mark.parametrize(
    ("result_field", "group_column", "group_values"),
    [
        ("per_plu", ArticleKey.PLU.value, [101, 102]),
        ("per_category", ArticleKey.CATEGORY.value, [1, 2]),
    ],
)
def test_run_calculates_metrics_for_each_group(
    backtester: ModelBacktester[object],
    raw_history: pd.DataFrame,
    result_field: str,
    group_column: str,
    group_values: list[int],
) -> None:
    result = backtester.run(raw_history)
    grouped = getattr(result, result_field).set_index(group_column)

    assert set(grouped.index) == set(group_values)
    assert grouped.loc[group_values[0], "support"] == 3
    assert grouped.loc[group_values[0], "actual_sum"] == pytest.approx(90.0)
    assert grouped.loc[group_values[0], "prediction_sum"] == pytest.approx(88.0)
    assert grouped.loc[group_values[0], "MAE"] == pytest.approx(22.0 / 3.0)
    assert grouped.loc[group_values[0], "WAPE"] == pytest.approx(22.0 / 90.0)
    assert grouped.loc[group_values[1], "support"] == 3
    assert grouped.loc[group_values[1], "actual_sum"] == pytest.approx(120.0)
    assert grouped.loc[group_values[1], "prediction_sum"] == pytest.approx(112.0)
    assert grouped.loc[group_values[1], "MAE"] == pytest.approx(4.0)
    assert grouped.loc[group_values[1], "WAPE"] == pytest.approx(12.0 / 120.0)


def test_run_rejects_empty_split_list(
    backtester: ModelBacktester[object],
    raw_history: pd.DataFrame,
    splitter: MagicMock,
    trainer_factory: MagicMock,
    matrix_builder: MagicMock,
) -> None:
    splitter.get_walk_forward_splits.return_value = []

    with pytest.raises(ValueError, match="folds"):
        backtester.run(raw_history)

    trainer_factory.assert_not_called()
    matrix_builder.build_train_evaluation.assert_not_called()
    matrix_builder.build_early_stopping_fold.assert_not_called()


@pytest.mark.parametrize("uses_early_stopping", [False, True])
def test_run_does_not_modify_input(
    backtester: ModelBacktester[object],
    raw_history: pd.DataFrame,
    strategy: MagicMock,
    uses_early_stopping: bool,
) -> None:
    strategy.uses_early_stopping = uses_early_stopping
    original = raw_history.copy(deep=True)

    backtester.run(raw_history)

    pd.testing.assert_frame_equal(raw_history, original)


@pytest.mark.parametrize("predictions", [np.array([1.0]), np.ones((2, 1))])
def test_run_rejects_wrong_prediction_shape(
    backtester: ModelBacktester[object],
    raw_history: pd.DataFrame,
    trainers: tuple[MagicMock, MagicMock],
    predictions: np.ndarray,
) -> None:
    trainers[0].predict.return_value = predictions

    with pytest.raises(ValueError, match="one prediction per validation row"):
        backtester.run(raw_history)


def test_prediction_frame_excludes_features_and_does_not_modify_matrix(
    raw_history: pd.DataFrame,
) -> None:
    matrix = _as_matrix(raw_history.iloc[2:4])
    matrix[PipelineKey.DEMAND_LAG_14D.value] = [3.0, 4.0]
    original = matrix.copy(deep=True)

    result = ModelBacktester._build_prediction_frame(
        validation_matrix=matrix,
        predictions=np.array([8.0, 22.0]),
        fold_number=1,
    )

    assert PipelineKey.DEMAND_LAG_14D.value not in result.columns
    pd.testing.assert_frame_equal(matrix, original)
    result.loc[result.index[0], PipelineKey.TARGET_DEMAND.value] = -1.0
    pd.testing.assert_frame_equal(matrix, original)


@pytest.mark.parametrize("uses_early_stopping", [False, True])
def test_run_propagates_training_errors(
    backtester: ModelBacktester[object],
    raw_history: pd.DataFrame,
    trainers: tuple[MagicMock, MagicMock],
    strategy: MagicMock,
    uses_early_stopping: bool,
) -> None:
    strategy.uses_early_stopping = uses_early_stopping
    trainers[0].fit.side_effect = RuntimeError("Training failed")
    trainers[0].fit_with_early_stopping.side_effect = RuntimeError("Training failed")

    with pytest.raises(RuntimeError, match="Training failed"):
        backtester.run(raw_history)

    trainers[0].predict.assert_not_called()
    trainers[1].fit.assert_not_called()
    trainers[1].fit_with_early_stopping.assert_not_called()


def test_run_walk_forward_with_real_components(
    dummy_raw_data: pd.DataFrame,
) -> None:
    strategy = XGBoostTrainingStrategy(
        n_estimators=20,
        early_stopping_rounds=2,
    )
    backtester = ModelBacktester(
        strategy=strategy,
        splitter=DataSplitter(n_splits=2),
        matrix_builder=TemporalMatrixBuilder(
            cleaning_config=HistoryCleanerConfig(winsorized_quantile=1.0),
        ),
    )

    result = backtester.run(dummy_raw_data)

    assert isinstance(result, BacktestResult)
    assert len(result.fold_metrics) == 2
    assert result.global_metrics["MAE"] >= 0.0
    assert not result.per_plu.empty
    assert not result.per_category.empty
    assert PipelineKey.BACKTEST_FOLD.value in result.predictions.columns
