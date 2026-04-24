from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LinearRegression
from training.models.exporter import ModelExporter


def test_model_exporter_saves_file(tmp_path: Path) -> None:
    """ " Tests if the ModelExporter correctly saves a model file to disk."""
    model = LinearRegression()
    x = np.array([[1], [2], [3]])
    y = np.array([2, 4, 6])
    model.fit(x, y)

    export_path = tmp_path / "test_export.joblib"
    exporter = ModelExporter()

    exporter.save(model, export_path)

    assert export_path.exists(), "Model file was not created at the specified path."
    assert export_path.stat().st_size > 0, "Model file is empty after saving."

    loaded_model = joblib.load(export_path)
    assert isinstance(
        loaded_model, LinearRegression
    ), "Loaded model is not of the expected type."
