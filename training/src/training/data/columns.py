from enum import Enum


class PipelineKey(Enum):
    DEMAND_RAW = "demand_raw"
    DEMAND_CLEANED = "demand_cleaned"
    WAS_IMPUTED = "was_imputed"
    WAS_WINSORIZED = "was_winsorized"
    RESTAURANT_TOTAL_DEMAND = "restaurant_total_demand"
