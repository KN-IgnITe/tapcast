import pandas as pd

from training.data.columns import PipelineKey
from training.data.mock_data_generator import ArticleKey, DayKey, WeatherKey


class TrainingMatrixBuilder:
    """
    TrainingMatrixBuilder is responsible for:
    1. converting cleaned_history into a final training matrix
    2. generating leakage-safe historical features with 14-day buffer
    3. moving quality flags from historical records into lag features
    4. calculating rolling medians and quality counters
    5. generating target_demand for supervised model training
    """

    def build(self, cleaned_history: pd.DataFrame) -> pd.DataFrame:
        """
        Build the final training matrix from cleaned history.
        Each output row represents one target date and one PLU.
        Historical features must not use data newer than target_date - 14 days
        """

        df_hist = self._prepare_history(cleaned_history)

        df_target = self._initialize_target_rows(df_hist)

        df_target = self._add_demand_lag_14d(df_target, df_hist)
        df_target = self._add_demand_lag_21d(df_target, df_hist)

        df_target = self._add_total_demand_lag_14d(df_target, df_hist)

        df_target = self._add_smart_lag(df_target, df_hist)

        df_target = self._add_plu_rolling_median_7d(df_target, df_hist)
        df_target = self._add_category_rolling_median_7d(df_target, df_hist)

        return self._format_output(df_target)

    def _prepare_history(self, cleaned_history: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare cleaned history for feature generation.
        Converts date column to datetime and sorts rows by date and PLU
        """

        df = cleaned_history.copy()
        df[DayKey.DATE.value] = pd.to_datetime(df[DayKey.DATE.value])
        return df.sort_values(by=[DayKey.DATE.value, ArticleKey.PLU.value]).reset_index(
            drop=True
        )

    def _initialize_target_rows(self, df_hist: pd.DataFrame) -> pd.DataFrame:
        """Initialize rows and map raw demand to target demand"""

        df_target = df_hist.copy()

        date_col = DayKey.DATE.value
        raw_demand_col = PipelineKey.DEMAND_RAW.value
        target_col = PipelineKey.TARGET_DEMAND.value

        df_target[PipelineKey.DAY_OF_MONTH.value] = df_target[date_col].dt.day
        df_target[target_col] = df_target[raw_demand_col]

        return df_target

    def _add_exact_lag(
        self,
        df_target: pd.DataFrame,
        df_hist: pd.DataFrame,
        lag_days: int,
        rename_map: dict[str, str],
        flag_cols: list[str],
    ) -> pd.DataFrame:
        """
        Add exact lag features for a fixed number of days.
        Copies demand_cleaned and quality flags from historical records
        located exactly lag_days before the target date.
        """

        date_col = DayKey.DATE.value
        plu_col = ArticleKey.PLU.value

        cols_to_keep = [date_col, plu_col] + list(rename_map.keys())
        lag_lookup = df_hist[cols_to_keep].copy()

        lag_lookup[date_col] = lag_lookup[date_col] + pd.Timedelta(days=lag_days)

        lag_lookup = lag_lookup.rename(columns=rename_map)

        merged = df_target.merge(
            lag_lookup,
            on=[date_col, plu_col],
            how="left",
        )

        if flag_cols:
            merged[flag_cols] = merged[flag_cols].fillna(0).astype(int)

        return merged

    def _add_demand_lag_14d(
        self,
        df_target: pd.DataFrame,
        df_hist: pd.DataFrame,
    ) -> pd.DataFrame:
        rename_map = {
            PipelineKey.DEMAND_CLEANED.value: PipelineKey.DEMAND_LAG_14D.value,
            PipelineKey.WAS_IMPUTED.value: PipelineKey.DEMAND_LAG_14D_WAS_IMPUTED.value,
            PipelineKey.WAS_WINSORIZED.value: (
                PipelineKey.DEMAND_LAG_14D_WAS_WINSORIZED.value
            ),
        }

        flag_cols = [
            PipelineKey.DEMAND_LAG_14D_WAS_IMPUTED.value,
            PipelineKey.DEMAND_LAG_14D_WAS_WINSORIZED.value,
        ]

        return self._add_exact_lag(
            df_target=df_target,
            df_hist=df_hist,
            lag_days=14,
            rename_map=rename_map,
            flag_cols=flag_cols,
        )

    def _add_demand_lag_21d(
        self,
        df_target: pd.DataFrame,
        df_hist: pd.DataFrame,
    ) -> pd.DataFrame:
        rename_map = {
            PipelineKey.DEMAND_CLEANED.value: PipelineKey.DEMAND_LAG_21D.value,
            PipelineKey.WAS_IMPUTED.value: PipelineKey.DEMAND_LAG_21D_WAS_IMPUTED.value,
            PipelineKey.WAS_WINSORIZED.value: (
                PipelineKey.DEMAND_LAG_21D_WAS_WINSORIZED.value
            ),
        }

        flag_cols = [
            PipelineKey.DEMAND_LAG_21D_WAS_IMPUTED.value,
            PipelineKey.DEMAND_LAG_21D_WAS_WINSORIZED.value,
        ]

        return self._add_exact_lag(
            df_target=df_target,
            df_hist=df_hist,
            lag_days=21,
            rename_map=rename_map,
            flag_cols=flag_cols,
        )

    def _add_total_demand_lag(
        self,
        df_target: pd.DataFrame,
        df_hist: pd.DataFrame,
        lag_days: int,
        rename_map: dict[str, str],
    ) -> pd.DataFrame:
        """
        Add lag feature for restaurant total demand.
        Copies restaurant_total_demand from historical records
        located exactly lag_days before the target date.
        """

        date_col = DayKey.DATE.value
        total_col = list(rename_map.keys())[0]

        daily_totals = df_hist[[date_col, total_col]].drop_duplicates(date_col).copy()
        daily_totals[date_col] = daily_totals[date_col] + pd.Timedelta(days=lag_days)
        daily_totals = daily_totals.rename(columns=rename_map)

        return df_target.merge(
            daily_totals,
            on=[date_col],
            how="left",
        )

    def _add_total_demand_lag_14d(
        self,
        df_target: pd.DataFrame,
        df_hist: pd.DataFrame,
    ) -> pd.DataFrame:

        rename_map = {
            PipelineKey.RESTAURANT_TOTAL_DEMAND.value: (
                PipelineKey.RESTAURANT_TOTAL_DEMAND_LAG_14D.value
            ),
        }

        return self._add_total_demand_lag(
            df_target=df_target,
            df_hist=df_hist,
            lag_days=14,
            rename_map=rename_map,
        )

    def _add_smart_lag(
        self,
        df_target: pd.DataFrame,
        df_hist: pd.DataFrame,
        max_backwards_limit: int = 28,
    ) -> pd.DataFrame:
        """
        Add smart lag feature based on the last similar historical day.
        Looks for a day that is 14 or more days before the target date.
        """

        date_col = DayKey.DATE.value
        plu_col = ArticleKey.PLU.value
        is_working_col = DayKey.IS_WORKING.value
        is_next_working_col = DayKey.IS_NEXT_DAY_WORKING.value

        smart_value_col = PipelineKey.DEMAND_LAST_SIMILAR_DAY.value
        smart_imputed_col = PipelineKey.DEMAND_LAST_SIMILAR_DAY_WAS_IMPUTED.value
        smart_winsorized_col = PipelineKey.DEMAND_LAST_SIMILAR_DAY_WAS_WINSORIZED.value

        cutoff_col = "_feature_cutoff_date"
        row_order_col = "_row_order"
        hist_date_col = "_smart_lag_history_date"

        hist_subset = df_hist[
            [
                date_col,
                plu_col,
                is_working_col,
                is_next_working_col,
                PipelineKey.DEMAND_CLEANED.value,
                PipelineKey.WAS_IMPUTED.value,
                PipelineKey.WAS_WINSORIZED.value,
            ]
        ].rename(
            columns={
                date_col: hist_date_col,
                PipelineKey.DEMAND_CLEANED.value: smart_value_col,
                PipelineKey.WAS_IMPUTED.value: smart_imputed_col,
                PipelineKey.WAS_WINSORIZED.value: smart_winsorized_col,
            }
        )

        df_merged = df_target.copy()
        df_merged[row_order_col] = range(len(df_merged))
        df_merged[cutoff_col] = df_merged[date_col] - pd.Timedelta(days=14)

        df_merged = df_merged.sort_values(cutoff_col)
        hist_subset = hist_subset.sort_values(hist_date_col)

        df_merged = pd.merge_asof(
            left=df_merged,
            right=hist_subset,
            left_on=cutoff_col,
            right_on=hist_date_col,
            by=[plu_col, is_working_col, is_next_working_col],
            direction="backward",
            tolerance=pd.Timedelta(days=max_backwards_limit),
        )

        df_merged[smart_imputed_col] = (
            df_merged[smart_imputed_col].fillna(0).astype(int)
        )

        df_merged[smart_winsorized_col] = (
            df_merged[smart_winsorized_col].fillna(0).astype(int)
        )

        return (
            df_merged.sort_values(row_order_col)
            .drop(columns=[row_order_col, cutoff_col, hist_date_col])
            .reset_index(drop=True)
        )

    def _add_plu_rolling_median_7d(
        self,
        df_target: pd.DataFrame,
        df_hist: pd.DataFrame,
    ) -> pd.DataFrame:

        rename_map = {
            PipelineKey.DEMAND_CLEANED.value: PipelineKey.PLU_ROLLING_MEDIAN_7D.value,
            PipelineKey.WAS_IMPUTED.value: (
                PipelineKey.PLU_ROLLING_MEDIAN_7D_IMPUTED_COUNT.value
            ),
            PipelineKey.WAS_WINSORIZED.value: (
                PipelineKey.PLU_ROLLING_MEDIAN_7D_WINSORIZED_COUNT.value
            ),
        }

        return self._add_plu_rolling_median(
            df_target=df_target,
            df_hist=df_hist,
            window=7,
            rename_map=rename_map,
        )

    def _add_plu_rolling_median(
        self,
        df_target: pd.DataFrame,
        df_hist: pd.DataFrame,
        window: int,
        rename_map: dict[str, str],
    ) -> pd.DataFrame:
        """
        Add PLU rolling median feature for the past window days.
        """

        count_cols = [
            rename_map[PipelineKey.WAS_IMPUTED.value],
            rename_map[PipelineKey.WAS_WINSORIZED.value],
        ]

        return self._compute_and_merge_rolling_features(
            df_target=df_target,
            df_source=df_hist,
            group_col=ArticleKey.PLU.value,
            window=window,
            rename_map=rename_map,
            count_cols=count_cols,
        )

    def _add_category_rolling_median_7d(
        self,
        df_target: pd.DataFrame,
        df_hist: pd.DataFrame,
    ) -> pd.DataFrame:

        rename_map = {
            PipelineKey.DEMAND_CLEANED.value: (
                PipelineKey.CATEGORY_ROLLING_MEDIAN_7D.value
            ),
            PipelineKey.WAS_IMPUTED.value: (
                PipelineKey.CATEGORY_ROLLING_MEDIAN_7D_IMPUTED_COUNT.value
            ),
            PipelineKey.WAS_WINSORIZED.value: (
                PipelineKey.CATEGORY_ROLLING_MEDIAN_7D_WINSORIZED_COUNT.value
            ),
        }

        return self._add_category_rolling_median(
            df_target=df_target,
            df_hist=df_hist,
            window=7,
            rename_map=rename_map,
        )

    def _add_category_rolling_median(
        self,
        df_target: pd.DataFrame,
        df_hist: pd.DataFrame,
        window: int,
        rename_map: dict[str, str],
    ) -> pd.DataFrame:
        """
        Add rolling median of daily category total demand and quality counters.
        """

        date_col = DayKey.DATE.value
        cat_col = ArticleKey.CATEGORY.value

        daily_cat_df = (
            df_hist.groupby([cat_col, date_col])[
                [
                    PipelineKey.DEMAND_CLEANED.value,
                    PipelineKey.WAS_IMPUTED.value,
                    PipelineKey.WAS_WINSORIZED.value,
                ]
            ]
            .sum()
            .reset_index()
        )

        count_cols = [
            rename_map[PipelineKey.WAS_IMPUTED.value],
            rename_map[PipelineKey.WAS_WINSORIZED.value],
        ]

        return self._compute_and_merge_rolling_features(
            df_target=df_target,
            df_source=daily_cat_df,
            group_col=cat_col,
            window=window,
            rename_map=rename_map,
            count_cols=count_cols,
        )

    def _compute_and_merge_rolling_features(
        self,
        df_target: pd.DataFrame,
        df_source: pd.DataFrame,
        group_col: str,
        window: int,
        rename_map: dict[str, str],
        count_cols: list[str],
    ) -> pd.DataFrame:
        """
        Compute rolling features
        based on the specified group column and merge into target.
        """

        date_col = DayKey.DATE.value
        clean_col = PipelineKey.DEMAND_CLEANED.value
        imputed_col = PipelineKey.WAS_IMPUTED.value
        winsorized_col = PipelineKey.WAS_WINSORIZED.value

        df_roll = df_source.sort_values([group_col, date_col]).set_index(date_col)

        rolling_features = (
            df_roll.groupby(group_col)[[clean_col, imputed_col, winsorized_col]]
            .rolling(f"{window}D")
            .agg(
                {
                    clean_col: "median",
                    imputed_col: "sum",
                    winsorized_col: "sum",
                }
            )
            .reset_index()
        )

        rolling_features = rolling_features.rename(columns=rename_map)
        rolling_features[date_col] = rolling_features[date_col] + pd.Timedelta(days=14)

        merged = df_target.merge(rolling_features, on=[date_col, group_col], how="left")
        merged[count_cols] = merged[count_cols].fillna(0).astype(int)

        return merged

    def _format_output(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Select and reorder final training matrix columns.

        Keeps only model input columns, technical date column and target demand.
        """

        expected_columns = [
            DayKey.DATE.value,
            ArticleKey.PLU.value,
            ArticleKey.CATEGORY.value,
            WeatherKey.AVG_TEMP.value,
            WeatherKey.TEMP_AMPLITUDE.value,
            WeatherKey.RAIN.value,
            DayKey.DAY_OF_WEEK.value,
            PipelineKey.DAY_OF_MONTH.value,
            DayKey.IS_WORKING.value,
            DayKey.IS_NEXT_DAY_WORKING.value,
            PipelineKey.DEMAND_LAG_14D.value,
            PipelineKey.DEMAND_LAG_14D_WAS_IMPUTED.value,
            PipelineKey.DEMAND_LAG_14D_WAS_WINSORIZED.value,
            PipelineKey.DEMAND_LAG_21D.value,
            PipelineKey.DEMAND_LAG_21D_WAS_IMPUTED.value,
            PipelineKey.DEMAND_LAG_21D_WAS_WINSORIZED.value,
            PipelineKey.RESTAURANT_TOTAL_DEMAND_LAG_14D.value,
            PipelineKey.DEMAND_LAST_SIMILAR_DAY.value,
            PipelineKey.DEMAND_LAST_SIMILAR_DAY_WAS_IMPUTED.value,
            PipelineKey.DEMAND_LAST_SIMILAR_DAY_WAS_WINSORIZED.value,
            PipelineKey.PLU_ROLLING_MEDIAN_7D.value,
            PipelineKey.PLU_ROLLING_MEDIAN_7D_IMPUTED_COUNT.value,
            PipelineKey.PLU_ROLLING_MEDIAN_7D_WINSORIZED_COUNT.value,
            PipelineKey.CATEGORY_ROLLING_MEDIAN_7D.value,
            PipelineKey.CATEGORY_ROLLING_MEDIAN_7D_IMPUTED_COUNT.value,
            PipelineKey.CATEGORY_ROLLING_MEDIAN_7D_WINSORIZED_COUNT.value,
            PipelineKey.TARGET_DEMAND.value,
        ]

        missing_columns = [col for col in expected_columns if col not in df.columns]

        if missing_columns:
            raise ValueError(f"Missing training matrix columns: {missing_columns}")

        output = df[expected_columns].copy()
        output.columns = expected_columns

        return output
