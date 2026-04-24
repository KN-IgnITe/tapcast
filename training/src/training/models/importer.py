from pathlib import Path
from typing import Any

import joblib


class ModelImporter:
    """Class reposnsible for loading the trained model from disk."""

    def load(self, file_path: Path | str) -> Any:
        """Loads the model from the specified file path.

        :param file_path: The path where the model is saved.
        :return: The loaded model.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Model file not found at {file_path}")

        return joblib.load(path)
