from pathlib import Path
from typing import Any, Type

import pytest
import numpy as np
from sklearn.datasets import make_regression
from sklearn.linear_model import Ridge
from xgboost import XGBRegressor

from training.models.local_io import LocalJoblibExporter, LocalJoblibImporter


@pytest.mark.parametrize("model_class", [Ridge, XGBRegressor])
def test_model_serialization_parity(tmp_path: Path, model_class: Type[Any]) -> None:
    """
    Tests integration (Parity Test),
    model before saving is identical to the one after import
    """

    X_train, y_train = make_regression(n_samples=100, n_features=5, random_state=42)
    X_test = np.random.rand(10, 5)

    original_model = model_class()
    original_model.fit(X_train, y_train)

    predictions_before = original_model.predict(X_test)

    model_path = tmp_path / f"test_{model_class.__name__}_parity.joblib"
    exporter = LocalJoblibExporter()
    exporter.save(original_model, model_path)

    importer = LocalJoblibImporter()
    loaded_model = importer.load(model_path)

    predictions_after = loaded_model.predict(X_test)

    np.testing.assert_allclose(
        predictions_before,
        predictions_after,
        err_msg=f"Parity test failed for {model_class.__name__}: "
        "predictions do not match!",
    )
