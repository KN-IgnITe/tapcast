from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any

from training.features.history_cleaner import HistoryCleaner, HistoryCleanerConfig


class CleanerArtifactKey(StrEnum):
    SCHEMA_VERSION = "schema_version"
    CONFIG = "config"
    WINSORIZATION_THRESHOLDS = "winsorization_thresholds"
    PLU_MEDIANS = "plu_medians"
    PLU_DOW_MEDIANS = "plu_dow_medians"
    POPULAR_PLU = "popular_plu"

    PLU = "plu"
    DAY_OF_WEEK = "day_of_week"
    THRESHOLD = "threshold"
    MEDIAN = "median"
    IS_POPULAR = "is_popular"


CURRENT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class HistoryCleanerArtifacts:
    """Stores fitted HistoryCleaner configuration and learned artifacts."""

    config: HistoryCleanerConfig
    winsorization_thresholds: dict[int, float]
    plu_medians: dict[int, float]
    plu_dow_medians: dict[tuple[int, int], float]
    popular_plu: dict[int, bool]

    @classmethod
    def from_cleaner(
        cls,
        cleaner: HistoryCleaner,
    ) -> "HistoryCleanerArtifacts":
        """Create artifacts from fitted HistoryCleaner."""

        if not cleaner.is_fitted:
            raise RuntimeError("Cannot export as unfitted HistoryCleaner.")

        return cls(
            config=cleaner.config,
            winsorization_thresholds=(cleaner.artifacts_winsorization_threshold.copy()),
            plu_medians=cleaner.artifacts_plu_median.copy(),
            plu_dow_medians=cleaner.artifacts_plu_dow_median.copy(),
            popular_plu=cleaner.artifacts_popular_plu.copy(),
        )

    def to_cleaner(self) -> HistoryCleaner:
        """Reconstruct a fitted HistoryCleaner."""

        cleaner = HistoryCleaner(config=self.config)

        cleaner.artifacts_winsorization_threshold = self.winsorization_thresholds.copy()
        cleaner.artifacts_plu_median = self.plu_medians.copy()
        cleaner.artifacts_plu_dow_median = self.plu_dow_medians.copy()
        cleaner.artifacts_popular_plu = self.popular_plu.copy()
        cleaner.is_fitted = True

        return cleaner

    def to_dict(self) -> dict[str, Any]:
        """Convert artifacts into JSON-compatible data."""

        return {
            CleanerArtifactKey.SCHEMA_VERSION.value: CURRENT_SCHEMA_VERSION,
            CleanerArtifactKey.CONFIG.value: asdict(self.config),
            CleanerArtifactKey.WINSORIZATION_THRESHOLDS.value: [
                {
                    CleanerArtifactKey.PLU.value: int(plu),
                    CleanerArtifactKey.THRESHOLD.value: float(threshold),
                }
                for plu, threshold in sorted(self.winsorization_thresholds.items())
            ],
            CleanerArtifactKey.PLU_MEDIANS.value: [
                {
                    CleanerArtifactKey.PLU.value: int(plu),
                    CleanerArtifactKey.MEDIAN.value: float(median),
                }
                for plu, median in sorted(self.plu_medians.items())
            ],
            CleanerArtifactKey.PLU_DOW_MEDIANS.value: [
                {
                    CleanerArtifactKey.PLU.value: int(plu),
                    CleanerArtifactKey.DAY_OF_WEEK.value: int(day_of_week),
                    CleanerArtifactKey.MEDIAN.value: float(median),
                }
                for (plu, day_of_week), median in sorted(self.plu_dow_medians.items())
            ],
            CleanerArtifactKey.POPULAR_PLU.value: [
                {
                    CleanerArtifactKey.PLU.value: int(plu),
                    CleanerArtifactKey.IS_POPULAR.value: bool(is_popular),
                }
                for plu, is_popular in sorted(self.popular_plu.items())
            ],
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "HistoryCleanerArtifacts":
        """Reconstruct artifacts from JSON-compatible data."""

        schema_version = data.get(CleanerArtifactKey.SCHEMA_VERSION.value)

        if schema_version != CURRENT_SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported cleaner artifact schema version: " f"{schema_version}"
            )

        config_data = data.get(CleanerArtifactKey.CONFIG.value)

        if not isinstance(config_data, dict):
            raise ValueError("Cleaner artifact config is missing or invalid.")

        return cls(
            config=HistoryCleanerConfig(**config_data),
            winsorization_thresholds={
                int(row[CleanerArtifactKey.PLU.value]): float(
                    row[CleanerArtifactKey.THRESHOLD.value]
                )
                for row in data[CleanerArtifactKey.WINSORIZATION_THRESHOLDS.value]
            },
            plu_medians={
                int(row[CleanerArtifactKey.PLU.value]): float(
                    row[CleanerArtifactKey.MEDIAN.value]
                )
                for row in data[CleanerArtifactKey.PLU_MEDIANS.value]
            },
            plu_dow_medians={
                (
                    int(row[CleanerArtifactKey.PLU.value]),
                    int(row[CleanerArtifactKey.DAY_OF_WEEK.value]),
                ): float(row[CleanerArtifactKey.MEDIAN.value])
                for row in data[CleanerArtifactKey.PLU_DOW_MEDIANS.value]
            },
            popular_plu={
                int(row[CleanerArtifactKey.PLU.value]): bool(
                    row[CleanerArtifactKey.IS_POPULAR.value]
                )
                for row in data[CleanerArtifactKey.POPULAR_PLU.value]
            },
        )
