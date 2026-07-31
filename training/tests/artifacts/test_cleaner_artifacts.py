import json
from typing import Any

import pandas as pd
import pytest

from training.artifacts.cleaner_artifacts import (
    CURRENT_SCHEMA_VERSION,
    CleanerArtifactKey,
    HistoryCleanerArtifacts,
)
from training.data.columns import PipelineKey
from training.data.mock_data_generator import ArticleKey, DayKey
from training.features.history_cleaner import HistoryCleaner, HistoryCleanerConfig


@pytest.fixture
def fitted_cleaner(raw_history_row_factory: Any) -> HistoryCleaner:
    raw_df = pd.DataFrame(
        [
            raw_history_row_factory("2026-01-05", 101, 1, 10, day_of_week=1),
            raw_history_row_factory("2026-01-12", 101, 1, 20, day_of_week=1),
            raw_history_row_factory("2026-01-19", 101, 1, 100, day_of_week=1),
            raw_history_row_factory("2026-01-19", 202, 2, 5, day_of_week=1),
        ]
    )

    cleaner = HistoryCleaner(
        config=HistoryCleanerConfig(
            winsorized_quantile=0.5,
            min_winsorization_observations=1,
            enable_oos_imputation=True,
        )
    )
    cleaner.fit(raw_df)
    return cleaner


def test_history_cleaner_artifacts_round_trip_preserves_values(
    fitted_cleaner: HistoryCleaner,
) -> None:
    artifacts = HistoryCleanerArtifacts.from_cleaner(fitted_cleaner)

    restored = HistoryCleanerArtifacts.from_dict(artifacts.to_dict())

    assert restored.config == artifacts.config
    assert restored.winsorization_thresholds == artifacts.winsorization_thresholds
    assert restored.plu_medians == artifacts.plu_medians
    assert restored.plu_dow_medians == artifacts.plu_dow_medians
    assert restored.popular_plu == artifacts.popular_plu


def test_history_cleaner_artifacts_to_dict_is_json_compatible(
    fitted_cleaner: HistoryCleaner,
) -> None:
    artifacts = HistoryCleanerArtifacts.from_cleaner(fitted_cleaner)

    encoded = json.dumps(artifacts.to_dict())
    decoded = json.loads(encoded)

    assert decoded[CleanerArtifactKey.SCHEMA_VERSION.value] == CURRENT_SCHEMA_VERSION
    assert isinstance(decoded[CleanerArtifactKey.PLU_DOW_MEDIANS.value], list)


def test_history_cleaner_artifacts_reconstruct_fitted_cleaner(
    fitted_cleaner: HistoryCleaner,
    raw_history_row_factory: Any,
) -> None:
    artifacts = HistoryCleanerArtifacts.from_cleaner(fitted_cleaner)
    restored_cleaner = artifacts.to_cleaner()

    future_df = pd.DataFrame(
        [
            raw_history_row_factory("2026-02-02", 101, 1, 0, day_of_week=1),
            raw_history_row_factory("2026-02-02", 202, 2, 5, day_of_week=1),
            raw_history_row_factory("2026-02-09", 101, 1, 100, day_of_week=1),
        ]
    )

    transformed = restored_cleaner.transform(future_df)
    imputed_row = transformed[
        (transformed[DayKey.DATE.value] == "2026-02-02")
        & (transformed[ArticleKey.PLU.value] == 101)
    ].iloc[0]
    peak_row = transformed[
        (transformed[DayKey.DATE.value] == "2026-02-09")
        & (transformed[ArticleKey.PLU.value] == 101)
    ].iloc[0]

    assert restored_cleaner.is_fitted
    assert imputed_row[PipelineKey.WAS_IMPUTED.value] == 1
    assert peak_row[PipelineKey.WAS_WINSORIZED.value] == 1


def test_history_cleaner_artifacts_reject_unfitted_cleaner() -> None:
    cleaner = HistoryCleaner()

    with pytest.raises(RuntimeError, match="unfitted HistoryCleaner"):
        HistoryCleanerArtifacts.from_cleaner(cleaner)


def test_history_cleaner_artifacts_reject_unsupported_schema(
    fitted_cleaner: HistoryCleaner,
) -> None:
    data = HistoryCleanerArtifacts.from_cleaner(fitted_cleaner).to_dict()
    data[CleanerArtifactKey.SCHEMA_VERSION.value] = CURRENT_SCHEMA_VERSION + 1

    with pytest.raises(ValueError, match="Unsupported cleaner artifact schema"):
        HistoryCleanerArtifacts.from_dict(data)
