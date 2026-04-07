import calendar
import json
import math
import random
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
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

    category_multipliers: Dict[int, float] = field(
        default_factory=lambda: {
            1: 2.8,  # 1 cocktails, alcohol
            2: 3.5,  # 2 beer
            3: 1.5,  # 3 coffee, snacks
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
    Product(plu=101, category=1, base_demand=50),
    Product(plu=102, category=1, base_demand=20),
    Product(plu=201, category=2, base_demand=100),
    Product(plu=305, category=3, base_demand=5),
]


class MockDataGenerator:
    products: List[Product]
    weather_cfg: WeatherConfig
    sales_cfg: SalesConfig
    weights: LogLinWeights

    def __init__(
        self,
        products: List[Product] = None,
        weather_cfg: WeatherConfig = WeatherConfig(),
        sales_cfg: SalesConfig = SalesConfig(),
        weights: LogLinWeights = LogLinWeights(),
    ):
        self.products = products if products is not None else DEFAULT_PRODUCTS
        self.weather_cfg = weather_cfg
        self.sales_cfg = sales_cfg
        self.weights = weights
        # Generator memory: key is PLU and date and the value is demand that day
        self.history: Dict[tuple[int, date], int] = {}

    def _is_working_day(self, date_obj: date) -> bool:
        return date_obj.weekday() < calendar.SATURDAY

    def _generate_weather(self) -> Dict[str, float]:
        """Generate random weather data for single day."""
        is_raining = random.random() < self.weather_cfg.rain_chance
        rain_amount = (
            random.uniform(0.0, self.weather_cfg.max_rain) if is_raining else 0.0
        )

        return {
            "avg_temp": round(
                random.uniform(self.weather_cfg.min_temp, self.weather_cfg.max_temp),
                self.weather_cfg.precision,
            ),
            "temp_amplitude": round(
                random.uniform(self.weather_cfg.min_amp, self.weather_cfg.max_amp),
                self.weather_cfg.precision,
            ),
            "rain": round(rain_amount, self.weather_cfg.precision),
        }

    def _get_day_multiplier(self, weekday: int, multiplier: float) -> float:
        if weekday == calendar.FRIDAY:
            return multiplier * self.sales_cfg.friday_multiplier
        elif weekday == calendar.SATURDAY:
            return multiplier
        elif weekday == calendar.SUNDAY:
            return 1.0 + (multiplier - 1.0) * self.sales_cfg.sunday_multiplier_offset
        else:
            return 1.0

    def _generate_article_data(
        self, product: Product, current_date: date, weather: Dict[str, float]
    ) -> Dict[str, float]:
        """Generate random data for single article, correlated based on actual calendar days"""
        cfg = self.sales_cfg
        today_weekday = current_date.weekday()

        # Historical data
        yesterday_date = current_date - timedelta(days=1)
        week_ago_date = current_date - timedelta(days=7)

        # Get real data or base demand
        real_yesterday = self.history.get(
            (product.plu, yesterday_date), product.base_demand
        )
        real_week_ago = self.history.get(
            (product.plu, week_ago_date), product.base_demand
        )

        peak_multiplier = cfg.category_multipliers.get(
            product.category, cfg.default_weekend_multiplier
        )
        day_multiplier = self._get_day_multiplier(today_weekday, peak_multiplier)
        beta_Day = math.log(day_multiplier) if day_multiplier > 0 else 0.0

        log_base = math.log(max(1, product.base_demand))
        log_yest = math.log(max(1, real_yesterday))
        log_week = math.log(max(1, real_week_ago))

        temp_effect = self.weights.temp * (
            weather["avg_temp"] - self.weather_cfg.neutral_temp
        )
        rain_effect = self.weights.rain * weather["rain"]

        linear_prediction = (
            log_base
            + temp_effect
            + rain_effect
            + beta_Day
            + self.weights.yesterday * (log_yest - log_base)
            + self.weights.week_ago * (log_week - log_base)
        )

        amount = int(random.lognormvariate(linear_prediction, cfg.demand_variance))
        # Save data to dict
        self.history[(product.plu, current_date)] = amount

        return {
            "PLU": product.plu,
            "category": product.category,
            "amount": amount,
            "yesterday_demand": real_yesterday,
            "week_ago_demand": real_week_ago,
        }

    def _generate_sales(
        self, current_date: date, weather: Dict[str, float]
    ) -> Dict[str, List[Dict[str, int]]]:
        """Generate sells section for current day"""
        articles = [
            self._generate_article_data(product, current_date, weather)
            for product in self.products
        ]

        return {"articles": articles}

    def _generate_single_day(self, current_date: date) -> Dict[str, Any]:
        next_date = current_date + timedelta(days=1)
        is_working = self._is_working_day(current_date)
        is_next_day_working = self._is_working_day(next_date)

        daily_weather = self._generate_weather()
        return {
            "weather": daily_weather,
            "sells": self._generate_sales(current_date, daily_weather),
            "date": current_date.strftime("%Y-%m-%d"),
            "day_of_week": current_date.isoweekday(),
            "is_working": is_working,
            "is_next_day_working": is_next_day_working,
        }

    def generate_mock_data(
        self, num_days: int = 30, start_date_str: str = "2026-04-01"
    ) -> Dict[str, List[Dict[str, Any]]]:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()

        day_data_list = [
            self._generate_single_day(start_date + timedelta(days=i))
            for i in range(num_days)
        ]

        return {"day_data": day_data_list}


if __name__ == "__main__":
    generator = MockDataGenerator()
    # Generate data
    mocked_json = generator.generate_mock_data(num_days=730)

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
