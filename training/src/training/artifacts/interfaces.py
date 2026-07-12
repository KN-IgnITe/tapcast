from pathlib import Path
from typing import Any, Protocol


class ArtifactExporter(Protocol):
    """Abstract base class for artifact exporters."""

    def save(self, artifact: Any, destination: Path | str) -> None: ...


class ArtifactImporter(Protocol):
    """Abstract base class for artifact importers."""

    def load(self, source: Path | str) -> Any: ...
