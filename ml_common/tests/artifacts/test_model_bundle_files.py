from ml_common.artifacts.model_bundle_files import (
    CLEANER_ARTIFACTS_FILE,
    METADATA_FILE,
    MODEL_BUNDLE_CONTENT_TYPES,
    MODEL_BUNDLE_FILES,
    MODEL_FILE,
    PREPROCESSOR_FILE,
    build_model_bundle_key,
)


def test_bundle_model_key_joins_prefix_and_file_name() -> None:
    result = build_model_bundle_key(
        prefix="demand-model/latest",
        file_name=MODEL_FILE,
    )

    assert result == "demand-model/latest/xgb_model.json"


def test_build_model_bundle_key_strips_extra_slashes() -> None:
    result = build_model_bundle_key(
        prefix="/demand-model/latest/", file_name=MODEL_FILE
    )

    assert result == "demand-model/latest/xgb_model.json"


def test_build_model_bundle_key_returns_file_name_for_empty_prefix() -> None:
    result = build_model_bundle_key(
        prefix="",
        file_name=MODEL_FILE,
    )

    assert result == MODEL_FILE


def test_model_bundle_files_contains_expcected_files() -> None:
    assert MODEL_BUNDLE_FILES == (
        MODEL_FILE,
        PREPROCESSOR_FILE,
        CLEANER_ARTIFACTS_FILE,
        METADATA_FILE,
    )


def test_model_bundle_content_types_contains_expected_types() -> None:
    assert MODEL_BUNDLE_CONTENT_TYPES == {
        MODEL_FILE: "application/json",
        CLEANER_ARTIFACTS_FILE: "application/json",
        METADATA_FILE: "application/json",
        PREPROCESSOR_FILE: "application/octet-stream",
    }
