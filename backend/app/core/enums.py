"""Domain enums shared by the persistence and wire-contract layers."""

from enum import StrEnum


class DocumentStatus(StrEnum):
    """Lifecycle stage of an uploaded document."""

    uploaded = "uploaded"
    indexing = "indexing"
    indexed = "indexed"
    error = "error"
