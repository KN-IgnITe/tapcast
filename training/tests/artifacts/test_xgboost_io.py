from pathlib import Path

import numpy as np
import pytest
from xgboost import XGBRegressor

from training.artifacts.xgboost_io import XGBoostExporter, XGBoostImporter


def test_xgboost_exporter_and_importer_preserve_predictions(
    tmp_path: Path,
) -> None:
    X = np.array(
        [
            [1.0, 0.0],
            [2.0, 1.0],
            [3.0, 0.0],
            [4.0, 1.0],
        ]
    )
    y = np.array([2.0, 4.0, 6.0, 8.0])

    model = XGBRegressor(
        n_estimators=3,
        max_depth=2,
        objective="reg:squarederror",
        random_state=42,
    )
    model.fit(X, y)

    path = tmp_path / "xgb_model.json"

    XGBoostExporter().save(model, path)
    loaded_model = XGBoostImporter().load(path)

    np.testing.assert_allclose(
        loaded_model.predict(X),
        model.predict(X),
    )


def test_xgboost_importer_raises_when_file_is_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        XGBoostImporter().load(tmp_path / "missing_xgb_model.json")
