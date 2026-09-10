from unittest.mock import MagicMock

import pandas as pd
import pytest
from ml_common.model.preprocessing.base import FeaturePreprocessor
from training.data.columns import PipelineKey
from training.data.data_splitter import DataSplitter
from training.data.mock_data_generator import ArticleKey, DayKey
from training.evaluation import early_stopping_selector as selector_module
from training.evaluation.early_stopping_selector import EarlyStoppingSelector
from training.features.history_cleaner import HistoryCleanerConfig
from training.features.temporal_matrix_builder import TemporalMatrixBuilder
from training.models.early_stopping_strategy import EarlyStoppingTrainingStrategy
from training.models.model_trainer import ModelTrainer
from training.models.xgboost_strategy import XGBoostTrainingStrategy


@pytest.fixture
def raw_history() -> pd.DataFrame:
    return pd.DataFrame(
        {
            DayKey.DATE.value: pd.date_range("2026-01-01", periods=4),
            ArticleKey.DEMAND.value: [10.0, 20.0, 30.0, 40.0],
        }
    )


@pytest.fixture
def splitter(raw_history: pd.DataFrame) -> MagicMock:
    mock = MagicMock(spec=DataSplitter)
    mock.get_inner_validation_split.return_value = (
        raw_history.iloc[:3].copy(),
        raw_history.iloc[3:].copy(),
    )
    return mock


@pytest.fixture
def train_matrix() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "feature": [1.0, 2.0, 3.0],
            PipelineKey.TARGET_DEMAND.value: [10.0, 20.0, 30.0],
        }
    )


@pytest.fixture
def early_stop_matrix() -> pd.DataFrame:
    return pd.DataFrame({"feature": [4.0], PipelineKey.TARGET_DEMAND.value: [40.0]})


@pytest.fixture
def matrix_builder(
    train_matrix: pd.DataFrame, early_stop_matrix: pd.DataFrame
) -> MagicMock:
    mock = MagicMock(spec=TemporalMatrixBuilder)
    mock.build_train_evaluation.return_value = (train_matrix, early_stop_matrix)
    return mock


@pytest.fixture
def strategy() -> MagicMock:
    mock = MagicMock(spec=EarlyStoppingTrainingStrategy)
    mock.selected_iteration.return_value = 137
    return mock


@pytest.fixture
def trainer() -> MagicMock:
    mock = MagicMock(spec=ModelTrainer)
    mock.model = object()
    return mock


@pytest.fixture
def trainer_factory(monkeypatch: pytest.MonkeyPatch, trainer: MagicMock) -> MagicMock:
    factory = MagicMock(return_value=trainer)
    monkeypatch.setattr(selector_module, "ModelTrainer", factory)
    return factory


@pytest.fixture
def selector(
    strategy: MagicMock,
    splitter: MagicMock,
    matrix_builder: MagicMock,
) -> EarlyStoppingSelector[object]:
    return EarlyStoppingSelector(
        strategy=strategy, splitter=splitter, matrix_builder=matrix_builder
    )


def test_select_builds_two_partitions_and_returns_strategy_iteration(
    selector: EarlyStoppingSelector[object],
    raw_history: pd.DataFrame,
    splitter: MagicMock,
    matrix_builder: MagicMock,
    train_matrix: pd.DataFrame,
    early_stop_matrix: pd.DataFrame,
    strategy: MagicMock,
    trainer: MagicMock,
    trainer_factory: MagicMock,
) -> None:
    result = selector.select(raw_history)

    assert result == 137
    splitter.get_inner_validation_split.assert_called_once()
    assert splitter.get_inner_validation_split.call_args.args[0] is raw_history
    raw_inner, raw_early_stop = splitter.get_inner_validation_split.return_value
    matrix_builder.build_train_evaluation.assert_called_once()
    builder_args = matrix_builder.build_train_evaluation.call_args.kwargs
    assert builder_args["raw_train"] is raw_inner
    assert builder_args["raw_evaluation"] is raw_early_stop
    trainer_factory.assert_called_once_with(strategy)
    trainer.fit_with_early_stopping.assert_called_once()
    fit_args = trainer.fit_with_early_stopping.call_args.kwargs
    assert fit_args["train_matrix"] is train_matrix
    assert fit_args["validation_matrix"] is early_stop_matrix
    strategy.selected_iteration.assert_called_once_with(trainer.model)
    trainer.fit.assert_not_called()
    trainer.predict.assert_not_called()
    splitter.get_final_test_split.assert_not_called()
    splitter.get_walk_forward_splits.assert_not_called()
    matrix_builder.build_early_stopping_fold.assert_not_called()


def test_select_creates_a_fresh_trainer_for_each_call(
    selector: EarlyStoppingSelector[object],
    raw_history: pd.DataFrame,
    strategy: MagicMock,
    trainer: MagicMock,
    trainer_factory: MagicMock,
) -> None:
    second_trainer = MagicMock(spec=ModelTrainer)
    second_trainer.model = object()
    trainer_factory.side_effect = [trainer, second_trainer]
    strategy.selected_iteration.side_effect = [137, 82]

    assert selector.select(raw_history) == 137
    assert selector.select(raw_history) == 82

    assert trainer_factory.call_count == 2
    trainer.fit_with_early_stopping.assert_called_once()
    second_trainer.fit_with_early_stopping.assert_called_once()
    calls = strategy.selected_iteration.call_args_list
    assert calls[0].args[0] is trainer.model
    assert calls[1].args[0] is second_trainer.model


@pytest.mark.parametrize("stage", ["split", "build", "fit", "select"])
def test_select_propagates_errors_without_continuing(
    selector: EarlyStoppingSelector[object],
    raw_history: pd.DataFrame,
    splitter: MagicMock,
    matrix_builder: MagicMock,
    strategy: MagicMock,
    trainer: MagicMock,
    trainer_factory: MagicMock,
    stage: str,
) -> None:
    stages = {
        "split": splitter.get_inner_validation_split,
        "build": matrix_builder.build_train_evaluation,
        "fit": trainer.fit_with_early_stopping,
        "select": strategy.selected_iteration,
    }
    error = RuntimeError(f"Failed at {stage}")
    stages[stage].side_effect = error

    with pytest.raises(RuntimeError, match=f"Failed at {stage}") as raised:
        selector.select(raw_history)

    assert raised.value is error
    stage_names = list(stages)
    remaining = stage_names.index(stage) + 1
    for name in stage_names[remaining:]:
        stages[name].assert_not_called()
    if stage in {"split", "build"}:
        trainer_factory.assert_not_called()
    trainer.predict.assert_not_called()


def test_select_works_with_real_trainer_and_fits_preprocessor_only_on_train(
    selector: EarlyStoppingSelector[object],
    raw_history: pd.DataFrame,
    strategy: MagicMock,
    train_matrix: pd.DataFrame,
    early_stop_matrix: pd.DataFrame,
) -> None:
    preprocessor = MagicMock(spec=FeaturePreprocessor)
    preprocessor.fit_transform.return_value = train_matrix[["feature"]].copy()
    preprocessor.transform.return_value = early_stop_matrix[["feature"]].copy()
    strategy.create_preprocessor.return_value = preprocessor
    fitted_model = object()
    strategy.fit_with_early_stopping.return_value = fitted_model
    original = raw_history.copy(deep=True)

    result = selector.select(raw_history)

    assert result == 137
    strategy.create_preprocessor.assert_called_once_with()
    preprocessor.fit_transform.assert_called_once()
    assert preprocessor.fit_transform.call_args.args[0] is train_matrix
    preprocessor.transform.assert_called_once()
    assert preprocessor.transform.call_args.args[0] is early_stop_matrix
    strategy.fit_with_early_stopping.assert_called_once()
    train, validation = strategy.fit_with_early_stopping.call_args.args
    pd.testing.assert_frame_equal(train.features, train_matrix[["feature"]])
    pd.testing.assert_frame_equal(validation.features, early_stop_matrix[["feature"]])
    pd.testing.assert_series_equal(
        train.target, train_matrix[PipelineKey.TARGET_DEMAND.value]
    )
    pd.testing.assert_series_equal(
        validation.target, early_stop_matrix[PipelineKey.TARGET_DEMAND.value]
    )
    strategy.selected_iteration.assert_called_once_with(fitted_model)
    strategy.fit.assert_not_called()
    strategy.predict.assert_not_called()
    pd.testing.assert_frame_equal(raw_history, original)


def test_select_returns_valid_tree_count_with_real_components(
    dummy_raw_data: pd.DataFrame,
) -> None:
    strategy = XGBoostTrainingStrategy(
        n_estimators=20,
        early_stopping_rounds=2,
    )
    selector = EarlyStoppingSelector(
        strategy=strategy,
        splitter=DataSplitter(n_splits=2),
        matrix_builder=TemporalMatrixBuilder(
            cleaning_config=HistoryCleanerConfig(winsorized_quantile=1.0),
        ),
    )

    tree_count = selector.select(dummy_raw_data)

    assert isinstance(tree_count, int)
    assert 1 <= tree_count <= strategy.n_estimators
