from dataclasses import dataclass
from pathlib import Path
from typing import Any


from training.artifacts.interfaces import ArtifactExporter, ArtifactImporter
from training.artifacts.joblib_io import JoblibExporter, JoblibImporter
from training.artifacts.json_io import JsonExporter, JsonImporter
from training.features.preprocessor import ModelPreprocessor

from training.features.history_cleaner import HistoryCleaner

from training.artifacts.cleaner_artifacts import HistoryCleanerArtifacts


@dataclass
class ProductionModelBundle:
    """Contains the model and all artifacts required for inference."""

    model: Any
    preprocessor: ModelPreprocessor
    cleaner: HistoryCleaner
    metadata: dict[str, Any]


class ProductionModelBundleExporter:
    """Exports a complete production model bundle to one directory."""

    def __init__(
        self,
        model_exporter: ArtifactExporter,
        model_filename: str,
    ) -> None:
        """Configure the exporter used to save the selected model type."""

        self.model_exporter = model_exporter
        self.model_filename = model_filename
        self.joblib_exporter = JoblibExporter()
        self.json_exporter = JsonExporter()

    def save(
        self,
        bundle: ProductionModelBundle,
        destination: Path | str,
    ) -> None:
        """Save the model, preprocessor, cleaner artifacts and metadata."""

        destination = Path(destination)
        destination.mkdir(parents=True, exist_ok=True)

        metadata = bundle.metadata.copy()
        metadata["model_file"] = self.model_filename

        self.model_exporter.save(
            bundle.model,
            destination / self.model_filename,
        )
        self.joblib_exporter.save(
            bundle.preprocessor,
            destination / "preprocessor.joblib",
        )
        cleaner_artifacts = HistoryCleanerArtifacts.from_cleaner(bundle.cleaner)
        self.json_exporter.save(
            cleaner_artifacts.to_dict(),
            destination / "cleaner_artifacts.json",
        )
        self.json_exporter.save(
            metadata,
            destination / "metadata.json",
        )


class ProductionModelBundleImporter:
    """Loads a complete production model bundle from one directory."""

    def __init__(
        self,
        model_importer: ArtifactImporter,
    ) -> None:
        """Configure the importer used to load the selected model type."""

        self.model_importer = model_importer
        self.joblib_importer = JoblibImporter()
        self.json_importer = JsonImporter()

    def load(
        self,
        source: Path | str,
    ) -> ProductionModelBundle:
        """Load and reconstruct all artifacts required for inference."""

        source = Path(source)

        metadata = self.json_importer.load(source / "metadata.json")

        model_filename = metadata.get("model_file")

        if not isinstance(model_filename, str):
            raise ValueError("Metadata does not contain a valid model_file.")

        model = self.model_importer.load(source / model_filename)
        preprocessor = self.joblib_importer.load(source / "preprocessor.joblib")
        cleaner_data = self.json_importer.load(source / "cleaner_artifacts.json")
        cleaner_artifacts = HistoryCleanerArtifacts.from_dict(cleaner_data)
        cleaner = cleaner_artifacts.to_cleaner()

        if not isinstance(preprocessor, ModelPreprocessor):
            raise TypeError("Loaded preprocessor has an invalid type.")

        return ProductionModelBundle(
            model=model,
            preprocessor=preprocessor,
            cleaner=cleaner,
            metadata=metadata,
        )
