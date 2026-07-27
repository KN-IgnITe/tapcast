from dataclasses import dataclass
from typing import cast

import numpy as np
import pandas as pd

from training.data.columns import PipelineKey
from training.data.mock_data_generator import ArticleKey, DayKey, WeatherKey


@dataclass(frozen=True)
class HistoryCleanerConfig:
    """Configuration of historical demand cleaning."""

    winsorized_quantile: float = 0.95
    min_winsorization_observations: int = 20
    enable_winsorization: bool = True
    enable_oos_imputation: bool = False

    def __post_init__(self) -> None:
        if not 0.0 < self.winsorized_quantile <= 1.0:
            raise ValueError(
                "winsorized_quantile must be greater than 0 and at most 1."
            )

        if self.min_winsorization_observations < 1:
            raise ValueError("min_winsorization_observations must be at least 1.")


class HistoryCleaner:
    """
    History cleaner is responsible for:
    1. generating column demand_raw and demand_cleaned
    2. Imputation of zeros with median with logical fallback
    3. Winsorization of demand_cleaned to remove outliers
    4. Generating flags was_imputed and was_winsorized
    """

    config: HistoryCleanerConfig
    artifacts_plu_dow_median: dict[tuple[int, int], float]
    artifacts_plu_median: dict[int, float]
    artifacts_popular_plu: dict[int, bool]
    artifacts_winsorization_threshold: dict[int, float]

    def __init__(
        self,
        config: HistoryCleanerConfig | None = None,
    ) -> None:
        self.config = config or HistoryCleanerConfig()

        self.artifacts_plu_dow_median = {}
        self.artifacts_plu_median = {}
        self.artifacts_popular_plu = {}
        self.artifacts_winsorization_threshold = {}
        self.is_fitted = False

    def clean(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """Fit cleaning artifacts and transform the same history."""

        return self.fit_transform(raw_df)

    def fit(self, raw_df: pd.DataFrame) -> "HistoryCleaner":
        """Learn cleaning artifacts from historical training data."""

        df = raw_df.copy()

        df = self._prepare_base_columns(df)
        df = self._add_total_demand(df)

        if self.config.enable_oos_imputation:
            self._fit_imputation_artifacts(df)
            df = self._apply_imputation(df)

        if self.config.enable_winsorization:
            self._fit_winsorization_artifacts(df)

        self.is_fitted = True

        return self

    def transform(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """Apply previously learned cleaning artifacts."""

        if not self.is_fitted:
            raise RuntimeError("Call fit before transform.")

        df = raw_df.copy()

        df = self._prepare_base_columns(df)
        df = self._add_total_demand(df)

        if self.config.enable_oos_imputation:
            df = self._apply_imputation(df)

        if self.config.enable_winsorization:
            df = self._apply_winsorization(df)

        return self._format_output(df)

    def fit_transform(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """Learn artifacts and transform historical training data."""

        self.fit(raw_df)
        return self.transform(raw_df)

    def _prepare_base_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Initialize new columns"""

        df = df.rename(columns={ArticleKey.DEMAND.value: PipelineKey.DEMAND_RAW.value})

        df[PipelineKey.DEMAND_CLEANED.value] = df[PipelineKey.DEMAND_RAW.value].astype(
            float
        )
        df[PipelineKey.WAS_IMPUTED.value] = 0
        df[PipelineKey.WAS_WINSORIZED.value] = 0

        return df

    def _add_total_demand(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add total raw demand for each day."""

        date_col = DayKey.DATE.value
        demand_raw_col = PipelineKey.DEMAND_RAW.value
        total_demand_col = PipelineKey.RESTAURANT_TOTAL_DEMAND.value

        df[total_demand_col] = df.groupby(date_col)[demand_raw_col].transform("sum")

        return df

    def _fit_imputation_artifacts(self, df: pd.DataFrame) -> None:
        """Learn PLU medians and popularity from training history."""

        plu_col = ArticleKey.PLU.value
        dow_col = DayKey.DAY_OF_WEEK.value
        clean_dem_col = PipelineKey.DEMAND_CLEANED.value

        sales_only = df[df[clean_dem_col] > 0]

        plu_dow_medians = sales_only.groupby([plu_col, dow_col])[clean_dem_col].median()

        plu_medians = sales_only.groupby(plu_col)[clean_dem_col].median()

        self.artifacts_plu_dow_median = cast(
            dict[tuple[int, int], float],
            plu_dow_medians.to_dict(),
        )
        self.artifacts_plu_median = cast(
            dict[int, float],
            plu_medians.to_dict(),
        )

        plu_history_medians = df.groupby(plu_col)[clean_dem_col].median()
        self.artifacts_popular_plu = cast(
            dict[int, bool],
            plu_history_medians.gt(2).to_dict(),
        )

    def _apply_imputation(self, df: pd.DataFrame) -> pd.DataFrame:
        """Impute suspicious zero demand using learned artifacts."""

        plu_col = ArticleKey.PLU.value
        dow_col = DayKey.DAY_OF_WEEK.value
        clean_dem_col = PipelineKey.DEMAND_CLEANED.value
        total_dem_col = PipelineKey.RESTAURANT_TOTAL_DEMAND.value
        imputed_col = PipelineKey.WAS_IMPUTED.value

        # If historical median demand for the PLU is greater than 2,
        # we consider it as popular and impute zeros with median,
        # otherwise we keep zeros as they are likely correct
        is_popular_plu = (
            df[plu_col].map(self.artifacts_popular_plu).fillna(False).astype(bool)
        )

        mask_oos = df[total_dem_col].gt(0) & df[clean_dem_col].eq(0) & is_popular_plu

        fallback_dow = pd.Series(
            df.set_index([plu_col, dow_col]).index.map(self.artifacts_plu_dow_median),
            index=df.index,
        )

        fallback_plu = df[plu_col].map(self.artifacts_plu_median)

        imputed_values = fallback_dow.fillna(fallback_plu).fillna(0)

        actual_imputation_mask = mask_oos & imputed_values.gt(0)

        df.loc[actual_imputation_mask, clean_dem_col] = imputed_values[
            actual_imputation_mask
        ]

        df.loc[actual_imputation_mask, imputed_col] = 1

        return df

    def _fit_winsorization_artifacts(self, df: pd.DataFrame) -> None:
        """Learn each PLU winsorization threshold from training history."""

        plu_col = ArticleKey.PLU.value
        clean_demand_col = PipelineKey.DEMAND_CLEANED.value

        positive_sales = df[df[clean_demand_col] > 0]

        grouped_sales = positive_sales.groupby(plu_col)[clean_demand_col]

        positive_counts = grouped_sales.size()

        thresholds = grouped_sales.quantile(self.config.winsorized_quantile)

        eligible_plu = positive_counts[
            positive_counts >= self.config.min_winsorization_observations
        ].index

        thresholds = thresholds.loc[eligible_plu]

        self.artifacts_winsorization_threshold = cast(
            dict[int, float],
            thresholds.to_dict(),
        )

    def _apply_winsorization(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cap demand using previously learned PLU thresholds."""

        plu_col = ArticleKey.PLU.value
        clean_dem_col = PipelineKey.DEMAND_CLEANED.value
        winsorized_col = PipelineKey.WAS_WINSORIZED.value

        winsorization_thresholds = df.groupby(plu_col)[clean_dem_col].quantile(
            self.winsorized_quantile
        )

        self.artifacts_winsorization_threshold = cast(
            dict[int, float],
            winsorization_thresholds.to_dict(),
        )
        threshold_series = (
            df[plu_col].map(self.artifacts_winsorization_threshold).fillna(np.inf)
        )

        mask_peak = df[clean_dem_col] > threshold_series

        if mask_peak.any():
            df.loc[mask_peak, clean_dem_col] = threshold_series[mask_peak]
            df.loc[mask_peak, winsorized_col] = 1

        return df

    def _format_output(self, df: pd.DataFrame) -> pd.DataFrame:
        """Select and reorder cleaned history columns."""

        expected_columns = [
            DayKey.DATE.value,
            ArticleKey.PLU.value,
            ArticleKey.CATEGORY.value,
            PipelineKey.DEMAND_RAW.value,
            PipelineKey.DEMAND_CLEANED.value,
            PipelineKey.WAS_IMPUTED.value,
            PipelineKey.WAS_WINSORIZED.value,
            PipelineKey.RESTAURANT_TOTAL_DEMAND.value,
            DayKey.DAY_OF_WEEK.value,
            DayKey.IS_WORKING.value,
            DayKey.IS_NEXT_DAY_WORKING.value,
            WeatherKey.AVG_TEMP.value,
            WeatherKey.TEMP_AMPLITUDE.value,
            WeatherKey.RAIN.value,
        ]

        return df[expected_columns]
