from pathlib import Path
from typing import Any

import joblib


class JoblibExporter:
    """Serializes a Python object using joblib."""

    def save(self, artifact: Any, destination: Path | str) -> None:
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(artifact, path)


class JoblibImporter:
    """Loads a Python object serialized with joblib."""

    def load(self, source: Path | str) -> Any:
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Model file not found at {source}")

        return joblib.load(path)
