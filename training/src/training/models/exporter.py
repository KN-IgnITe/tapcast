from pathlib import Path
from typing import Any

import joblib


class ModelExporter:
    """Class responsible for saving the trained model to disk."""

    def save(self, model: Any, file_path: Path | str) -> None:
        """Saves the model to the specified file path.

        :param model: The trained model to be saved.
        :param file_path: The path where the model should be saved.
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        joblib.dump(model, path)
