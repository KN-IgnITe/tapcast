from pathlib import Path
from typing import Mapping, Protocol


class ModelBundleStore(Protocol):
    """Storage interface for for model bundles."""

    def upload_bundle_from_dir(self, source_dir: Path, prefix: str) -> None: ...

    def download_bundle_to_dir(self, target_dir: Path, prefix: str) -> None: ...

    def upload_bundle_bytes(
        self,
        files: Mapping[str, bytes],
        prefix: str,
    ) -> None: ...

    def download_bundle_bytes(self, prefix: str) -> dict[str, bytes]: ...

    def bundle_exists(self, prefix: str) -> bool: ...
