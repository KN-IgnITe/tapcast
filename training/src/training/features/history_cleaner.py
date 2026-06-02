from typing import Dict, Tuple
import numpy as np
import pandas as pd

from training.data.columns import PipelineKey
from training.data.mock_data_generator import ArticleKey, DayKey, WeatherKey


class HistoryCleaner:
    """
    History cleaner is responsible for:
    1. generating column demand_raw and demand_cleaned
    2. Imputation of zeros with median with logical fallback
    3. Winsorization of demand_cleaned to remove outliers
    4. Generating flags was_imputed and was_winsorized
    """

    winsorized_quantile: float

    artifacts_plu_dow_median: Dict[Tuple[int, int], float]
    artifacts_plu_median: Dict[int, float]
    artifacts_winsorization_threshold: Dict[int, float]

    def __init__(self, winsorized_quantile: float = 0.95) -> None:
        self.winsorized_quantile = winsorized_quantile
        self.artifacts_plu_dow_median = {}
        self.artifacts_plu_median = {}
        self.artifacts_winsorization_threshold = {}

    def clean(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        df = raw_df.copy()

        df = self._prepare_base_columns(df)

        df = self._add_total_demand(df)

        df = self._impute_out_of_stock(df)

        df = self._winsorize_demand(df)

        return self._format_output(df)

    def _prepare_base_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Initialize new columns"""

        df = df.rename(columns={ArticleKey.DEMAND.value: PipelineKey.DEMAND_RAW.value})

        df[PipelineKey.DEMAND_CLEANED.value] = df[PipelineKey.DEMAND_RAW.value]
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

    def _impute_out_of_stock(self, df: pd.DataFrame) -> pd.DataFrame:
        """Impute suspicious zero demand values using PLU medians."""

        plu_col = ArticleKey.PLU.value
        dow_col = DayKey.DAY_OF_WEEK.value
        clean_dem_col = PipelineKey.DEMAND_CLEANED.value
        total_dem_col = PipelineKey.RESTAURANT_TOTAL_DEMAND.value
        imputed_col = PipelineKey.WAS_IMPUTED.value

        sales_only = df[df[clean_dem_col] > 0]

        plu_dow_medians = sales_only.groupby([plu_col, dow_col])[clean_dem_col].median()

        plu_medians = sales_only.groupby(plu_col)[clean_dem_col].median()

        self.artifacts_plu_dow_median = plu_dow_medians.to_dict()
        self.artifacts_plu_median = plu_medians.to_dict()

        plu_history_medians = df.groupby(plu_col)[clean_dem_col].median()

        # if historicla median demand for the PLU is greater than 2,
        # we consider it as popular and impute zeros with median,
        # otherwise we keep zeros as they are likely correct
        is_popular_plu = df[plu_col].map(plu_history_medians).fillna(0).gt(2)

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

    def _winsorize_demand(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cap demand_cleaned values above each PLU quantile threshold."""

        plu_col = ArticleKey.PLU.value
        clean_dem_col = PipelineKey.DEMAND_CLEANED.value
        winsorized_col = PipelineKey.WAS_WINSORIZED.value

        winsorization_thresholds = df.groupby(plu_col)[clean_dem_col].quantile(
            self.winsorized_quantile
        )

        self.artifacts_winsorization_threshold = winsorization_thresholds.to_dict()

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
