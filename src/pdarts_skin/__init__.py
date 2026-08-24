"""Maintained reproducibility utilities for skin-lesion transfer studies."""

from .config import DatasetConfig, load_dataset_config
from .data import ManifestRecord, read_manifest, validate_manifest
from .metrics import accuracy, confusion_matrix, weighted_f1
from .splits import assign_patient_grouped, validate_patient_isolation

__all__ = [
    "DatasetConfig",
    "ManifestRecord",
    "accuracy",
    "assign_patient_grouped",
    "confusion_matrix",
    "load_dataset_config",
    "read_manifest",
    "validate_manifest",
    "validate_patient_isolation",
    "weighted_f1",
]

__version__ = "0.1.0"
