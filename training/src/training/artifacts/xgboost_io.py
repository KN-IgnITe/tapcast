from pathlib import Path

from xgboost import XGBRegressor


class XGBoostExporter:
    """Exports an XGBoost model using its native format."""

    def save(self, model: XGBRegressor, destination: Path | str) -> None:
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        model.save_model(path)


class XGBoostImporter:
    """Loads an XGBoost model saved in its native format."""

    def load(self, source: Path | str) -> XGBRegressor:
        path = Path(source)

        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {path}")

        model = XGBRegressor()
        model.load_model(path)
        return model
