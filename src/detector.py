"""Detector configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .utils import broadcast_to_grid, ensure_non_negative, validate_probability_like


@dataclass(frozen=True)
class DetectorConfig:
    """Minimal detector parameter container."""

    qe: float | list[float]
    dark_current_e_s_pix: float
    read_noise_e_pix: float
    n_pix: int

    def qe_curve(self, lam_nm: np.ndarray) -> np.ndarray:
        """Return the detector quantum efficiency sampled on the wavelength grid."""
        qe_curve = broadcast_to_grid(self.qe, lam_nm, name="qe")
        if np.any((qe_curve < 0.0) | (qe_curve > 1.0)):
            raise ValueError("Detector QE must lie in [0, 1].")
        return qe_curve


def build_detector_config(cfg: dict) -> DetectorConfig:
    """Validate and build a detector configuration dataclass."""
    if int(cfg["n_pix"]) <= 0:
        raise ValueError("n_pix must be a positive integer.")
    ensure_non_negative("dark_current_e_s_pix", float(cfg["dark_current_e_s_pix"]))
    ensure_non_negative("read_noise_e_pix", float(cfg["read_noise_e_pix"]))
    if np.isscalar(cfg["qe"]):
        validate_probability_like("qe", float(cfg["qe"]))
    return DetectorConfig(
        qe=cfg["qe"],
        dark_current_e_s_pix=float(cfg["dark_current_e_s_pix"]),
        read_noise_e_pix=float(cfg["read_noise_e_pix"]),
        n_pix=int(cfg["n_pix"]),
    )
