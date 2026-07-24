MODEL_FILE = "xgb_model.json"
PREPROCESSOR_FILE = "preprocessor.joblib"
CLEANER_ARTIFACTS_FILE = "cleaner_artifacts.json"
METADATA_FILE = "metadata.json"

MODEL_BUNDLE_FILES: tuple[str, ...] = (
    MODEL_FILE,
    PREPROCESSOR_FILE,
    CLEANER_ARTIFACTS_FILE,
    METADATA_FILE,
)

MODEL_BUNDLE_CONTENT_TYPES: dict[str, str] = {
    MODEL_FILE: "application/json",
    CLEANER_ARTIFACTS_FILE: "application/json",
    METADATA_FILE: "application/json",
    PREPROCESSOR_FILE: "application/octet-stream",
}


def build_model_bundle_key(prefix: str, file_name: str) -> str:
    """Build an S3 object key for a model bundle file."""

    normalized_prefix = prefix.strip("/")

    if not normalized_prefix:
        return file_name

    return f"{normalized_prefix}/{file_name}"
