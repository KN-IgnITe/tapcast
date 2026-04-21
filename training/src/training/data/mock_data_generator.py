import calendar
import json
import math
import random
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum, IntEnum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ProductCategory(IntEnum):
    COCKTAILS = 1
    BEER = 2
    COFFEE_SNACKS = 3


class WeatherKey(str, Enum):
    AVG_TEMP = "avg_temp"
    TEMP_AMPLITUDE = "temp_amplitude"
    RAIN = "rain"


class ArticleKey(str, Enum):
    PLU = "PLU"
    CATEGORY = "category"
    DEMAND = "demand"
    YESTERDAY_DEMAND = "yesterday_demand"
    WEEK_AGO_DEMAND = "week_ago_demand"


class DayKey(str, Enum):
    WEATHER = "weather"
    SELLS = "sells"
    DATE = "date"
    DAY_OF_WEEK = "day_of_week"
    IS_WORKING = "is_working"
    IS_NEXT_DAY_WORKING = "is_next_day_working"
    DAY_DATA = "day_data"


@dataclass
class Product:
    plu: int
    category: ProductCategory
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
    neutral_temp: float = 15.0


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

    category_multipliers: Dict[ProductCategory, float] = field(
        default_factory=lambda: {
            ProductCategory.COCKTAILS: 2.8,  # 1 cocktails, alcohol
            ProductCategory.BEER: 3.5,  # 2 beer
            ProductCategory.COFFEE_SNACKS: 1.5,  # 3 coffee, snacks
        }
    )


@dataclass(frozen=True)
class LogLinWeights:
    temp: float = 0.05
    rain: float = -0.15
    yesterday: float = 0.15
    week_ago: float = 0.25


# Category 1 - cocktails,alcohol 2 - beer, 3 -coffee, snacks
DEFAULT_PRODUCTS = [
    Product(plu=101, category=ProductCategory.COCKTAILS, base_demand=50),
    Product(plu=102, category=ProductCategory.BEER, base_demand=20),
    Product(plu=201, category=ProductCategory.BEER, base_demand=100),
    Product(plu=305, category=ProductCategory.COFFEE_SNACKS, base_demand=5),
]


class WeatherGenerator:
    cfg: WeatherConfig

    def __init__(self, cfg: WeatherConfig) -> None:
        self.cfg = cfg

    def generate(self) -> Dict[str, float]:
        is_raining = random.random() < self.cfg.rain_chance
        rain_amount = random.uniform(0.0, self.cfg.max_rain) if is_raining else 0.0

        return {
            WeatherKey.AVG_TEMP: round(
                random.uniform(self.cfg.min_temp, self.cfg.max_temp), self.cfg.precision
            ),
            WeatherKey.TEMP_AMPLITUDE: round(
                random.uniform(self.cfg.min_amp, self.cfg.max_amp), self.cfg.precision
            ),
            WeatherKey.RAIN: round(rain_amount, self.cfg.precision),
        }


class DemandGenerator:
    products: List[Product]
    sales_cfg: SalesConfig
    weights: LogLinWeights
    weather_cfg: WeatherConfig
    history: Dict[tuple[int, date], int]

    def __init__(
        self,
        products: List[Product],
        sales_cfg: SalesConfig,
        weights: LogLinWeights,
        wearter_cfg: WeatherConfig,
    ) -> None:
        self.products = products
        self.sales_cfg = sales_cfg
        self.weights = weights
        self.weather_cfg = wearter_cfg
        self.history: Dict[tuple[int, date], int] = {}

    def _get_day_multiplier(self, weekday: int, multiplier: float) -> float:
        if weekday == calendar.FRIDAY:
            return multiplier * self.sales_cfg.friday_multiplier
        elif weekday == calendar.SATURDAY:
            return multiplier
        elif weekday == calendar.SUNDAY:
            return 1.0 + (multiplier - 1.0) * self.sales_cfg.sunday_multiplier_offset
        return 1.0

    def generate(
        self, current_date: date, weather: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        sells = []
        today_weekday = current_date.weekday()
        yesterday_date = current_date - timedelta(days=1)
        weak_ago_date = current_date - timedelta(days=7)

        for product in self.products:
            real_yesterday = self.history.get(
                (product.plu, yesterday_date), product.base_demand
            )
            real_week_ago = self.history.get(
                (product.plu, weak_ago_date), product.base_demand
            )

            peak_multiplier = self.sales_cfg.category_multipliers.get(
                product.category, self.sales_cfg.default_weekend_multiplier
            )
            day_multiplier = self._get_day_multiplier(today_weekday, peak_multiplier)
            beta_day = math.log(day_multiplier) if day_multiplier > 0 else 0.0

            log_base = math.log(max(1, product.base_demand))
            log_yest = math.log(max(1, real_yesterday))
            log_week = math.log(max(1, real_week_ago))

            temp_effect = self.weights.temp * (
                weather[WeatherKey.AVG_TEMP] - self.weather_cfg.neutral_temp
            )
            rain_effect = self.weights.rain * weather[WeatherKey.RAIN]

            linear_prediction = (
                log_base
                + temp_effect
                + rain_effect
                + beta_day
                + self.weights.yesterday * (log_yest - log_base)
                + self.weights.week_ago * (log_week - log_base)
            )

            demand = int(
                random.lognormvariate(linear_prediction, self.sales_cfg.demand_variance)
            )
            self.history[(product.plu, current_date)] = demand

            articles_data: Dict[str, Any] = {
                ArticleKey.PLU: product.plu,
                ArticleKey.CATEGORY: product.category,
                ArticleKey.DEMAND: demand,
                ArticleKey.YESTERDAY_DEMAND: real_yesterday,
                ArticleKey.WEEK_AGO_DEMAND: real_week_ago,
            }

            sells.append(articles_data)

        return sells


class MockDataOrchestrator:
    """Orchestrator for generating mock data, keeping history and correlations"""

    products: List[Product]
    weather_gen: WeatherGenerator
    demand_gen: DemandGenerator

    def __init__(
        self,
        products: Optional[List[Product]] = None,
        weather_cfg: WeatherConfig = WeatherConfig(),
        sales_cfg: SalesConfig = SalesConfig(),
        weights: LogLinWeights = LogLinWeights(),
    ) -> None:
        self.products = products if products is not None else DEFAULT_PRODUCTS
        self.weather_gen = WeatherGenerator(weather_cfg)
        self.demand_gen = DemandGenerator(
            self.products, sales_cfg, weights, weather_cfg
        )

    @staticmethod
    def _is_working_day(date_obj: date) -> bool:
        return date_obj.weekday() < calendar.SATURDAY

    def _generate_single_day(self, current_date: date) -> Dict[str, Any]:
        daily_weather = self.weather_gen.generate()
        articles_data = self.demand_gen.generate(current_date, daily_weather)

        return {
            DayKey.DATE: current_date.strftime("%Y-%m-%d"),
            DayKey.DAY_OF_WEEK: current_date.isoweekday(),
            DayKey.IS_WORKING: self._is_working_day(current_date),
            DayKey.IS_NEXT_DAY_WORKING: self._is_working_day(
                current_date + timedelta(days=1)
            ),
            DayKey.WEATHER: daily_weather,
            DayKey.SELLS: articles_data,
        }

    def generate_mock_data(
        self, num_days: int = 30, start_date_str: str = "2026-04-01"
    ) -> Dict[str, List[Dict[str, Any]]]:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()

        day_data_list = [
            self._generate_single_day(start_date + timedelta(days=i))
            for i in range(num_days)
        ]

        return {DayKey.DAY_DATA: day_data_list}


def save_mock_data_to_json(
    data: Dict[str, Any], file_name: str = "mock_data.json"
) -> None:
    current_file_path = Path(__file__).resolve()
    training_dir = current_file_path.parents[3]

    output_dir = training_dir / "data" / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / file_name

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Mock data saved to {output_file}")


if __name__ == "__main__":
    orchestrator = MockDataOrchestrator()
    mock_data = orchestrator.generate_mock_data(num_days=730)
    save_mock_data_to_json(mock_data)
