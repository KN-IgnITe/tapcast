from typing import Any

import pandas as pd

from training.data.columns import PipelineKey
from training.data.mock_data_generator import ArticleKey, DayKey
from training.features.history_cleaner import HistoryCleanerConfig
from training.features.temporal_matrix_builder import TemporalMatrixBuilder


def test_temporal_builder_fits_cleaner_only_on_train_partition(
    raw_history_row_factory: Any,
) -> None:
    train_dates = pd.date_range("2026-01-01", periods=30, freq="D")
    evaluation_dates = pd.date_range("2026-01-31", periods=15, freq="D")

    raw_train = pd.DataFrame(
        [
            raw_history_row_factory(
                date,
                plu=101,
                category=1,
                demand=10 + index % 11,
            )
            for index, date in enumerate(train_dates)
        ]
    )
    raw_evaluation = pd.DataFrame(
        [
            raw_history_row_factory(date, plu=101, category=1, demand=1000)
            for date in evaluation_dates
        ]
    )

    builder = TemporalMatrixBuilder(
        cleaning_config=HistoryCleanerConfig(winsorized_quantile=1.0)
    )
    train_matrix, evaluation_matrix = builder.build_train_evaluation(
        raw_train,
        raw_evaluation,
    )

    last_evaluation_row = evaluation_matrix[
        evaluation_matrix[DayKey.DATE.value] == evaluation_dates[-1]
    ].iloc[0]

    assert evaluation_matrix[PipelineKey.TARGET_DEMAND.value].eq(1000).all()
    assert evaluation_matrix[PipelineKey.DEMAND_LAG_14D.value].notna().all()
    assert last_evaluation_row[PipelineKey.DEMAND_LAG_14D.value] == 20
    assert (
        train_matrix[DayKey.DATE.value].max()
        < evaluation_matrix[DayKey.DATE.value].min()
    )


def test_build_training_returns_matrix_and_fitted_cleaner(
    raw_history_row_factory: Any,
) -> None:
    dates = pd.date_range("2026-01-01", periods=30, freq="D")
    raw_history = pd.DataFrame(
        [
            raw_history_row_factory(
                date,
                plu=101,
                category=1,
                demand=10 + index % 11,
            )
            for index, date in enumerate(dates)
        ]
    )
    config = HistoryCleanerConfig(winsorized_quantile=1.0)
    builder = TemporalMatrixBuilder(cleaning_config=config)

    matrix, cleaner = builder.build_training(raw_history)

    assert len(matrix) == len(raw_history)
    assert cleaner.is_fitted
    assert cleaner.config == config
    assert cleaner.artifacts_winsorization_threshold[101] == 20
    assert (
        matrix[PipelineKey.TARGET_DEMAND.value].tolist()
        == raw_history[ArticleKey.DEMAND.value].tolist()
    )
