import pandas as pd

from training.data.mock_data_generator import DayKey
from training.features.history_cleaner import HistoryCleaner, HistoryCleanerConfig
from training.features.training_matrix_builder import TrainingMatrixBuilder


class TemporalMatrixBuilder:
    """Build leakage-safe matrices from chronological raw-data partitions."""

    def __init__(
        self,
        cleaning_config: HistoryCleanerConfig | None = None,
    ) -> None:
        self.cleaning_config = cleaning_config or HistoryCleanerConfig()

    def build_train_evaluation(
        self,
        raw_train: pd.DataFrame,
        raw_evaluation: pd.DataFrame,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Fit on raw train and build train/evaluation matrices."""

        partitions = self._build_partitions(
            raw_fit_history=raw_train,
            raw_partitions={
                "train": raw_train,
                "evaluation": raw_evaluation,
            },
        )

        return partitions["train"], partitions["evaluation"]

    def build_early_stopping_fold(
        self,
        raw_inner_train: pd.DataFrame,
        raw_early_stop: pd.DataFrame,
        raw_outer_validation: pd.DataFrame,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Build inner-train, early-stop and untouched outer matrices."""

        partitions = self._build_partitions(
            raw_fit_history=raw_inner_train,
            raw_partitions={
                "inner_train": raw_inner_train,
                "early_stop": raw_early_stop,
                "outer_validation": raw_outer_validation,
            },
        )

        return (
            partitions["inner_train"],
            partitions["early_stop"],
            partitions["outer_validation"],
        )

    def _build_partitions(
        self,
        raw_fit_history: pd.DataFrame,
        raw_partitions: dict[str, pd.DataFrame],
    ) -> dict[str, pd.DataFrame]:
        """Apply frozen cleaning artifacts and split the resulting matrix."""

        cleaner = HistoryCleaner(config=self.cleaning_config)
        cleaner.fit(raw_fit_history)

        cleaned_parts = [
            cleaner.transform(partition) for partition in raw_partitions.values()
        ]
        cleaned_history = pd.concat(
            cleaned_parts,
            ignore_index=True,
        )

        matrix = TrainingMatrixBuilder().build(cleaned_history)

        return {
            name: self._select_partition(matrix, raw_partition)
            for name, raw_partition in raw_partitions.items()
        }

    def _select_partition(
        self,
        matrix: pd.DataFrame,
        raw_partition: pd.DataFrame,
    ) -> pd.DataFrame:
        """Select matrix rows belonging to raw partition dates."""

        date_col = DayKey.DATE.value
        partition_dates = pd.to_datetime(raw_partition[date_col]).unique()

        selected = matrix[pd.to_datetime(matrix[date_col]).isin(partition_dates)]

        return selected.reset_index(drop=True)

    def build_training(
        self,
        raw_history: pd.DataFrame,
    ) -> tuple[pd.DataFrame, HistoryCleaner]:
        """Build a training matrix from all available history."""

        cleaner = HistoryCleaner(config=self.cleaning_config)
        cleaned_history = cleaner.fit_transform(raw_history)

        matrix = TrainingMatrixBuilder().build(cleaned_history)
        return matrix, cleaner
