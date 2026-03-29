"""Shared utility helpers for array handling, validation, and file output."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np


def ensure_positive(name: str, value: float) -> float:
    """Validate that a scalar input is strictly positive."""
    if value <= 0.0:
        raise ValueError(f"{name} must be > 0, got {value}.")
    return value


def ensure_non_negative(name: str, value: float) -> float:
    """Validate that a scalar input is non-negative."""
    if value < 0.0:
        raise ValueError(f"{name} must be >= 0, got {value}.")
    return value


def validate_probability_like(name: str, value: float) -> float:
    """Validate a scalar throughput-like quantity lies in [0, 1]."""
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must lie in [0, 1], got {value}.")
    return value


def as_numpy_1d(values: float | Iterable[float], name: str = "values") -> np.ndarray:
    """Convert scalar or iterable input to a one-dimensional float array."""
    arr = np.asarray(values, dtype=float)
    if arr.ndim == 0:
        arr = arr.reshape(1)
    if arr.ndim != 1:
        raise ValueError(f"{name} must be scalar or 1D, got ndim={arr.ndim}.")
    return arr


def broadcast_to_grid(values: float | Iterable[float], lam_nm: np.ndarray, name: str) -> np.ndarray:
    """Broadcast scalar or wavelength-sized input onto a wavelength grid."""
    arr = np.asarray(values, dtype=float)
    if arr.ndim == 0:
        return np.full_like(lam_nm, float(arr), dtype=float)
    if arr.shape != lam_nm.shape:
        raise ValueError(f"{name} must be scalar or have shape {lam_nm.shape}, got {arr.shape}.")
    return arr.astype(float)


def wavelength_grid_from_config(wavelength_cfg: dict) -> np.ndarray:
    """Build the wavelength grid in nm from config settings."""
    start_nm = ensure_positive("wavelength.start_nm", float(wavelength_cfg["start_nm"]))
    stop_nm = ensure_positive("wavelength.stop_nm", float(wavelength_cfg["stop_nm"]))
    step_nm = ensure_positive("wavelength.step_nm", float(wavelength_cfg["step_nm"]))
    if stop_nm < start_nm:
        raise ValueError("wavelength.stop_nm must be >= wavelength.start_nm.")
    n_step = int(round((stop_nm - start_nm) / step_nm))
    lam_nm = start_nm + np.arange(n_step + 1, dtype=float) * step_nm
    return lam_nm


def delta_lambda_nm(lam_nm: np.ndarray) -> np.ndarray:
    """Return per-bin wavelength spacing in nm for numeric integration."""
    lam_nm = as_numpy_1d(lam_nm, name="lam_nm")
    if lam_nm.size < 2:
        raise ValueError("lam_nm must contain at least two samples.")
    delta_nm = np.gradient(lam_nm)
    return delta_nm


def band_average(values: np.ndarray) -> float:
    """Compute an arithmetic band average for wavelength-sampled arrays."""
    arr = as_numpy_1d(values, name="values")
    return float(np.mean(arr))


def ensure_dir(path: str | Path) -> Path:
    """Create a directory if needed and return it as a Path."""
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def resolve_path(root: str | Path, relative_path: str) -> Path:
    """Resolve a config-relative path against a root directory."""
    return Path(root).joinpath(relative_path).resolve()
