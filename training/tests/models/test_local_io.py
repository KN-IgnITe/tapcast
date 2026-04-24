from pathlib import Path

import joblib
import numpy as np
import pytest
from sklearn.linear_model import LinearRegression
from training.models.local_io import LocalJoblibExporter, LocalJoblibImporter


def test_local_joblib_exporter_saves_file(tmp_path: Path) -> None:
    """ " Tests if the ModelExporter correctly saves a model file to disk."""
    model = LinearRegression()
    x = np.array([[1], [2], [3]])
    y = np.array([2, 4, 6])
    model.fit(x, y)

    export_path = tmp_path / "test_export.joblib"

    exporter = LocalJoblibExporter()

    exporter.save(model, export_path)

    assert export_path.exists(), "Model file was not created at the specified path."
    assert export_path.stat().st_size > 0, "Model file is empty after saving."

    loaded_model = joblib.load(export_path)
    assert isinstance(
        loaded_model, LinearRegression
    ), "Loaded model is not of the expected type."


def test_local_joblib_importer_loads_model(tmp_path: Path) -> None:
    """ " Tests if the ModelImporter correctly loads a model file from disk."""
    model = LinearRegression()
    # fake weights to make sure the model is loaded correctly
    model.coef_ = np.array([2.0])
    model.intercept_ = 10.0

    import_path = tmp_path / "test_import.joblib"
    joblib.dump(model, import_path)

    importer = LocalJoblibImporter()

    loaded_model = importer.load(import_path)

    assert loaded_model is not None, "Model was not loaded successfully."
    assert isinstance(
        loaded_model, LinearRegression
    ), "Loaded model is not of the expected type."
    assert np.allclose(
        loaded_model.coef_, model.coef_
    ), "Loaded model coefficients do not match the original model."


def test_local_joblib_importer_raises_error_if_file_missing() -> None:
    """
    Tests if ModelImporter raises FileNotFoundError,
    when the specified model file does not exist.
    """

    importer = LocalJoblibImporter()

    with pytest.raises(FileNotFoundError):
        importer.load("non_existent_model.joblib")
