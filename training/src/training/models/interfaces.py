from pathlib import Path
from typing import Any, Protocol


class ModelExporter(Protocol):
    """Abstract base class for model exporters."""

    def save(sel, model: Any, destination: Path | str) -> None: ...


class ModelImporter(Protocol):
    """Abstract base class for model importers."""

    def load(self, source: Path | str) -> Any: ...
