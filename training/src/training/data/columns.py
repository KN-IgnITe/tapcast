from enum import Enum


class PipelineKey(Enum):
    DEMAND_RAW = "demand_raw"
    DEMAND_CLEANED = "demand_cleaned"
    WAS_IMPUTED = "was_imputed"
    WAS_WINSORIZED = "was_winsorized"
    RESTAURANT_TOTAL_DEMAND = "restaurant_total_demand"

    DAY_OF_MONTH = "day_of_month"

    DEMAND_LAG_14D = "demand_lag_14d"
    DEMAND_LAG_14D_WAS_IMPUTED = "demand_lag_14d_was_imputed"
    DEMAND_LAG_14D_WAS_WINSORIZED = "demand_lag_14d_was_winsorized"

    DEMAND_LAG_21D = "demand_lag_21d"
    DEMAND_LAG_21D_WAS_IMPUTED = "demand_lag_21d_was_imputed"
    DEMAND_LAG_21D_WAS_WINSORIZED = "demand_lag_21d_was_winsorized"

    DEMAND_LAST_SIMILAR_DAY = "demand_last_similar_day"
    DEMAND_LAST_SIMILAR_DAY_WAS_IMPUTED = "demand_last_similar_day_was_imputed"
    DEMAND_LAST_SIMILAR_DAY_WAS_WINSORIZED = "demand_last_similar_day_was_winsorized"

    PLU_ROLLING_MEDIAN_7D = "plu_rolling_median_7d"
    PLU_ROLLING_MEDIAN_7D_IMPUTED_COUNT = "plu_rolling_median_7d_imputed_count"
    PLU_ROLLING_MEDIAN_7D_WINSORIZED_COUNT = "plu_rolling_median_7d_winsorized_count"

    CATEGORY_ROLLING_MEDIAN_7D = "category_rolling_median_7d"
    CATEGORY_ROLLING_MEDIAN_7D_IMPUTED_COUNT = (
        "category_rolling_median_7d_imputed_count"
    )
    CATEGORY_ROLLING_MEDIAN_7D_WINSORIZED_COUNT = (
        "category_rolling_median_7d_winsorized_count"
    )

    RESTAURANT_TOTAL_DEMAND_LAG_14D = "restaurant_total_demand_lag_14d"

    TARGET_DEMAND = "target_demand"
