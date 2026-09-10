from ml_common.model.feature_schema import FeatureSchema

DEMAND_MODEL_FEATURE_COLUMNS_V1: tuple[str, ...] = (
    "PLU",
    "category",
    "avg_temp",
    "temp_amplitude",
    "rain",
    "day_of_week",
    "day_of_month",
    "is_working",
    "is_next_day_working",
    "demand_lag_14d",
    "demand_lag_14d_was_imputed",
    "demand_lag_14d_was_winsorized",
    "demand_lag_21d",
    "demand_lag_21d_was_imputed",
    "demand_lag_21d_was_winsorized",
    "restaurant_total_demand_lag_14d",
    "demand_last_similar_day",
    "demand_last_similar_day_was_imputed",
    "demand_last_similar_day_was_winsorized",
    "plu_rolling_median_7d",
    "plu_rolling_median_7d_imputed_count",
    "plu_rolling_median_7d_winsorized_count",
    "category_rolling_median_7d",
    "category_rolling_median_7d_imputed_count",
    "category_rolling_median_7d_winsorized_count",
)

DEMAND_FEATURE_SCHEMA_V1 = FeatureSchema(
    name="demand",
    version=1,
    columns=DEMAND_MODEL_FEATURE_COLUMNS_V1,
    categorical_columns=("PLU", "category"),
)
