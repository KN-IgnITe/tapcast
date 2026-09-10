from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ml_common.model.model_kind import ModelKind
from ml_common.model.preprocessing.base import FeaturePreprocessor

from training.artifacts.cleaner_artifacts import HistoryCleanerArtifacts
from training.artifacts.interfaces import ArtifactExporter, ArtifactImporter
from training.artifacts.joblib_io import JoblibExporter, JoblibImporter
from training.artifacts.json_io import JsonExporter, JsonImporter
from training.features.history_cleaner import HistoryCleaner


@dataclass
class ProductionModelBundle:
    """Contains the model and all artifacts required for inference."""

    model: Any
    model_kind: ModelKind
    preprocessor: FeaturePreprocessor
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
        metadata["model_kind"] = bundle.model_kind.value
        metadata["feature_schema"] = {
            "name": bundle.preprocessor.schema.name,
            "version": bundle.preprocessor.schema.version,
        }

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
        """Load a trusted bundle and validate its preprocessing metadata."""

        source = Path(source)

        metadata = self.json_importer.load(source / "metadata.json")

        if not isinstance(metadata, dict):
            raise ValueError("Bundle metadata must be a JSON object.")

        model_filename = metadata.get("model_file")

        if not isinstance(model_filename, str):
            raise ValueError("Metadata does not contain a valid model_file.")

        if Path(model_filename).name != model_filename:
            raise ValueError("model_file must be a filename, not a path.")

        model_kind_value = metadata.get("model_kind")

        if not isinstance(model_kind_value, str):
            raise ValueError("Metadata does not contain a valid model_kind.")

        model_kind = ModelKind(model_kind_value)
        preprocessor = self.joblib_importer.load(source / "preprocessor.joblib")

        if not isinstance(preprocessor, FeaturePreprocessor):
            raise ValueError("Loaded preprocessor has an ivalid type.")

        expected_schema = {
            "name": preprocessor.schema.name,
            "version": preprocessor.schema.version,
        }

        if metadata.get("feature_schema") != expected_schema:
            raise ValueError("Metadata feature_schema does not match preprocessor.")

        cleaner_data = self.json_importer.load(source / "cleaner_artifacts.json")
        cleaner = HistoryCleanerArtifacts.from_dict(cleaner_data).to_cleaner()
        model = self.model_importer.load(source / model_filename)

        return ProductionModelBundle(
            model=model,
            model_kind=model_kind,
            preprocessor=preprocessor,
            cleaner=cleaner,
            metadata=metadata,
        )
