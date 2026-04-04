import calendar
from datetime import date, datetime, timedelta
from dataclasses import dataclass, field
import json
from pathlib import Path
import random
from typing import Any, Dict, List


@dataclass
class Product:
    plu: int
    category: int
    base_demand: int

@dataclass(frozen=True)
class WeatherConfig:
    min_temp: float = -5.0
    max_temp: float = 30.0
    min_amp: float = -8.0
    max_amp: float = 8.0
    max_rain: float = 15.0
    rain_chance: float = 0.3
    precision: int = 1

@dataclass(frozen=True)
class SalesConfig:
    demand_variance: float = 0.2
    trend_modifier_min: float = 0.8
    trend_modifier_max: float = 1.2

    # Day multipliers
    friday_multiplier: float = 0.85
    default_weekend_multiplier: float = 2.0
    sunday_multiplier_offset: float = 0.2

    # Demand weights
    base_demand_weight: float = 0.6
    week_ago_demand_weight: float = 0.25
    yesterday_demand_weight: float = 0.15

    category_multipliers: Dict[int, float] = field(default_factory=lambda: {
        1: 2.8, #1 cocktails, alcohol
        2: 3.5, #2 beer
        3: 1.5 #3 coffee, snacks
    })

# Category 1 - cocktails,alcohol 2 - beer, 3 -coffee, snacks
DEFAULT_PRODUCTS =  [
    Product(plu=101, category=1, base_demand=50),
    Product(plu=102, category=1, base_demand=20),
    Product(plu=201, category=2, base_demand=100),
    Product(plu=305, category=3, base_demand=5)
]    


def _is_working_day(date_obj: date) -> bool:
    return date_obj.weekday() < calendar.SATURDAY

def _generate_weather(cfg: WeatherConfig = WeatherConfig()) -> Dict[str, float]:
    """Generate random weather data for single day."""

    is_raining = random.random() < cfg.rain_chance
    rain_amount = random.uniform(0.0, cfg.max_rain) if is_raining else 0.0

    return {
        "avg_temp": round(random.uniform(cfg.min_temp, cfg.max_temp), cfg.precision),
        "temp_amplitude": round(random.uniform(cfg.min_amp, cfg.max_amp), cfg.precision),
        "rain": round(rain_amount, cfg.precision)
    }


def _generate_article_data(product: Product, current_date: date, cfg: SalesConfig = SalesConfig()) -> Dict[str, float]:
    """Generate random data for single article, correlated based on actual calendar days"""

    def _get_day_multiplier(weekday: int, multiplier: float) -> float:
        if weekday == calendar.FRIDAY:
            return multiplier * cfg.friday_multiplier
        elif weekday == calendar.SATURDAY:
            return multiplier
        elif weekday == calendar.SUNDAY:
            return 1.0 + (multiplier - 1.0) * cfg.sunday_multiplier_offset
        else:
            return 1.0
        
    def _get_demand(base: float) -> int:
        return max(0, int(random.gauss(base, base * cfg.demand_variance)))
    
    today_weekday = current_date.weekday()
    yesterday_weekday = (today_weekday - 1) % 7


    peek_multiplier = cfg.category_multipliers.get(product.category, cfg.default_weekend_multiplier)

    # Weekly trend
    trend_modifier = random.uniform(cfg.trend_modifier_min, cfg.trend_modifier_max)
    adjusted_base = product.base_demand * trend_modifier

    raw_week_ago = _get_demand(adjusted_base)
    raw_yesterday = _get_demand(adjusted_base)

    # Weighted expected demand for today
    today_expected = (adjusted_base * cfg.base_demand_weight) + (raw_week_ago * cfg.week_ago_demand_weight) + (raw_yesterday * cfg.yesterday_demand_weight)
    raw_today = _get_demand(today_expected)

    # Apply specific day multipliers
    amount = int(raw_today * _get_day_multiplier(today_weekday, peek_multiplier))
    week_ago_demand = int(raw_week_ago * _get_day_multiplier(today_weekday, peek_multiplier))
    yesterday_demand = int(raw_yesterday * _get_day_multiplier(yesterday_weekday, peek_multiplier))
            
    return {
        "PLU": product.plu,
        "category": product.category,
        "amount": amount,
        "yesterday_demand": yesterday_demand,
        "week_ago_demand": week_ago_demand
    }

def _generate_sales(products: List[Product], current_date: date) -> Dict[str, List[Dict[str, int]]]:
    """Generate sells section for current day"""
    articles = [ _generate_article_data(product, current_date) for product in products ]
    
    return {"articles": articles}

def _generate_single_day(current_date: date, products: List[Product]) -> Dict[str, Any]:
    next_date = current_date + timedelta(days=1)

    is_working = _is_working_day(current_date)
    is_next_day_working = _is_working_day(next_date)

    return {
        "weather": _generate_weather(),
        "sells": _generate_sales(products, current_date),
        "date": current_date.strftime("%Y-%m-%d"),
        "day_of_week": current_date.isoweekday(),
        "is_working": is_working,
        "is_next_day_working": is_next_day_working
    }

def generate_mock_data(
        num_days: int = 30,
        start_date_str: str = "2026-04-01",
        products: List[Product] = None
) -> Dict[str, List[Dict[str, Any]]]:
    
    if products is None:
        products = DEFAULT_PRODUCTS

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()

    day_data_list = [
        _generate_single_day(start_date + timedelta(days=i), products)
        for i in range(num_days)
    ]

    return {"day_data": day_data_list}

if __name__ == "__main__":
    # Generate data
    mocked_json = generate_mock_data()
    
    current_file_path = Path(__file__).resolve()
    training_root_dir = current_file_path.parents[3]

    # Final path
    output_dir = training_root_dir / "data" / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "mocked_data.json"

    # Save to file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(mocked_json, f, indent=2, ensure_ascii=False)

    print(f"Data was generated and saved: {output_file.absolute()}")    
