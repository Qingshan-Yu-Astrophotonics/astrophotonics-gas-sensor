"""Simplified sky background model utilities."""

from __future__ import annotations

import numpy as np

from .utils import broadcast_to_grid


def sky_photon_flux_per_nm_arcsec2(lam_nm: np.ndarray, sky_cfg: dict) -> np.ndarray:
    """Return the sky photon background on the wavelength grid."""
    model = sky_cfg.get("model", "constant")
    if model != "constant":
        if "values" not in sky_cfg:
            raise ValueError("Non-constant sky model requires a 'values' field.")
        return broadcast_to_grid(sky_cfg["values"], lam_nm, name="sky.values")

    value = float(sky_cfg["value_photons_s_m2_nm_arcsec2"])
    if value < 0.0:
        raise ValueError("Sky background must be non-negative.")
    return np.full_like(lam_nm, value, dtype=float)
