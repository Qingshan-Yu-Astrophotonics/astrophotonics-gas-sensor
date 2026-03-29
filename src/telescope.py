"""Telescope geometry and mirror train throughput helpers."""

from __future__ import annotations

import numpy as np

from .utils import ensure_non_negative, ensure_positive, validate_probability_like


def effective_collecting_area(D_m: float, D_obs_m: float) -> float:
    """Compute the effective collecting area in square meters."""
    ensure_positive("D_m", D_m)
    ensure_non_negative("D_obs_m", D_obs_m)
    if D_obs_m >= D_m:
        raise ValueError("D_obs_m must be smaller than D_m.")
    return float(np.pi * (D_m**2 - D_obs_m**2) / 4.0)


def mirror_train_throughput(reflectivity: float, n_mirrors: int) -> float:
    """Compute the net mirror train throughput."""
    validate_probability_like("reflectivity", reflectivity)
    if n_mirrors < 0:
        raise ValueError("n_mirrors must be >= 0.")
    return float(reflectivity**n_mirrors)
