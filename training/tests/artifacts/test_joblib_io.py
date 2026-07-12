from pathlib import Path

import numpy as np
import pytest
from sklearn.linear_model import LinearRegression

from training.artifacts.joblib_io import JoblibExporter, JoblibImporter


def test_joblib_exporter_and_importer_round_trip_model(tmp_path: Path) -> None:
    model = LinearRegression()
    X = np.array([[1.0], [2.0], [3.0]])
    y = np.array([2.0, 4.0, 6.0])
    model.fit(X, y)

    path = tmp_path / "model.joblib"

    JoblibExporter().save(model, path)
    loaded_model = JoblibImporter().load(path)

    assert isinstance(loaded_model, LinearRegression)
    np.testing.assert_allclose(
        loaded_model.predict(X),
        model.predict(X),
    )


def test_joblib_importer_raises_when_file_is_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        JoblibImporter().load(tmp_path / "missing.joblib")
