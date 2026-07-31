import json
from pathlib import Path
from typing import Any


class JsonExporter:
    """Serializes dictionary artifacts to a JSON file."""

    def save(
        self,
        value: dict[str, Any],
        destination: Path | str,
    ) -> None:
        path = Path(destination)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as file:
            json.dump(value, file, indent=2)


class JsonImporter:
    """Loads dictionary artifacts from a JSON file."""

    def load(self, source: Path | str) -> dict[str, Any]:
        path = Path(source)

        if not path.exists():
            raise FileNotFoundError(f"Artifact not found {path}")

        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
