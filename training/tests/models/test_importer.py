from pathlib import Path

import joblib
import numpy as np
import pytest
from sklearn.linear_model import LinearRegression
from training.models.importer import ModelImporter


def test_model_importer_loads_file(tmp_path: Path) -> None:
    """ " Tests if the ModelImporter correctly loads a model file from disk."""
    model = LinearRegression()
    # fake weights to make sure the model is loaded correctly
    model.coef_ = np.array([2.0])
    model.intercept_ = 10.0

    import_path = tmp_path / "test_import.joblib"
    joblib.dump(model, import_path)

    importer = ModelImporter()

    loaded_model = importer.load(import_path)

    assert loaded_model is not None, "Model was not loaded successfully."
    assert isinstance(
        loaded_model, LinearRegression
    ), "Loaded model is not of the expected type."
    assert np.allclose(
        loaded_model.coef_, model.coef_
    ), "Loaded model coefficients do not match the original model."


def test_model_importer_file_not_found() -> None:
    """
    Tests if ModelImporter raises FileNotFoundError,
    when the specified model file does not exist.
    """

    importer = ModelImporter()

    with pytest.raises(FileNotFoundError):
        importer.load("non_existent_model.joblib")
