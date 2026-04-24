from pathlib import Path
from typing import Any

import joblib

from training.models.interfaces import ModelExporter, ModelImporter


class LocalJoblibExporter(ModelExporter):
    """Saves the trained model to disk using joblib."""

    def save(self, model: Any, destination: Path | str) -> None:
        """Saves the model to the specified destination.

        :param model: The trained model to be saved.
        :param destination: The file path where the model should be saved.
        """
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, path)


class LocalJoblibImporter(ModelImporter):
    """Loads the trained model from disk using joblib."""

    def load(self, source: Path | str) -> Any:
        """Loads the model from the specified source.

        :param source: The file path where the model is saved.
        :return: The loaded model.
        """
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Model file not found at {source}")

        return joblib.load(path)
