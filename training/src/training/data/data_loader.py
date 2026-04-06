
import json
from pathlib import Path
from typing import Any, Dict, List
import pandas as pd

class DemandDataLoader:

    file_path: Path

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)

    def load_and_process(self) -> pd.DataFrame:
       """Main method to load data from JSON and change it to flat matrix (DataFrame)"""

       raw_data = self._read_json()
       df = self._flatten_data(raw_data)

       df['date'] = pd.to_datetime(df['date'])

       return df
    
    def _read_json(self) -> Dict[str, Any]:
        """Load data from JSON file and manage errors if file is not found or JSON is invalid"""
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        with open(self.file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
        
    def _flatten_data(self, data: Dict[str, Any]) -> pd.DataFrame:    
        """Flatten the nested JSON structure into a flat DataFrame"""
        flattened_records: List[Dict[str, Any]] = []

        day_data_list = data.get("day_data", [])

        if not day_data_list:
            raise ValueError("No 'day_data' found in the JSON data")
        
        for day in day_data_list:
          base_features = self._extract_day_features(day)

          for article in day.get("sells", {}).get("articles", []):
              row = base_features.copy()
              row.update(self._extract_article_features(article))
              flattened_records.append(row)

        return pd.DataFrame(flattened_records)       
    
    def _extract_day_features(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features related to the day (date, day of week, working day)"""

        weather_features = self._extract_weather_features(data.get("weather", {}))

        features =  {
            "date": data.get("date"),
            "day_of_week": data.get("day_of_week"),
            "is_working": data.get("is_working"),
            "is_next_day_working": data.get("is_next_day_working"),
        }
        features.update(weather_features)
        return features
    
    def _extract_weather_features(self, weather: Dict[str, Any]) -> Dict[str, float]:
        return {
            "avg_temp": float(weather.get("avg_temp", 0.0)),
            "temp_amplitude": float(weather.get("temp_amplitude", 0.0)),
            "rain": float(weather.get("rain", 0.0)),
        }
    
    def _extract_article_features(self, article: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "PLU": article.get("PLU"),
            "category": article.get("category"),
            "yesterday_demand": article.get("yesterday_demand"),
            "week_ago_demand": article.get("week_ago_demand"),
            "amount": article.get("amount"),
        }

if __name__ == "__main__":
    data_path = Path(__file__).parents[3] / "data" / "raw" / "mocked_data.json"

    try:
        loader = DemandDataLoader(data_path)
        df_flat = loader.load_and_process()

        print(f"Data loaded and processed successfully. DataFrame shape: {df_flat.shape}")
        print(df_flat.head())
    except Exception as e:
        print(f"An error occurred druing data loading: {e}")    