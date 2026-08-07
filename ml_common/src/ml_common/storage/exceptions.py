class StorageError(RuntimeError):
    """Base error for storage operations."""
    

class StorageObjectNotFoundError(StorageError):
    """Raised when an object does not exist in storage."""    