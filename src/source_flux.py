"""AB magnitude to photon flux conversions."""

from __future__ import annotations

import numpy as np

from .constants import AB_ZEROPOINT_JY, JY_TO_W_M2_HZ, NM_TO_M, PLANCK_J_S
from .utils import as_numpy_1d


def ab_mag_to_fnu_w_m2_hz(m_ab: float) -> float:
    """Convert AB magnitude to spectral flux density F_nu in SI units."""
    return float(AB_ZEROPOINT_JY * JY_TO_W_M2_HZ * 10.0 ** (-0.4 * m_ab))


def fnu_to_photon_flux_per_nm(fnu_w_m2_hz: float, lam_nm: np.ndarray) -> np.ndarray:
    """Convert F_nu to photon flux density in photons / s / m^2 / nm."""
    lam_nm = as_numpy_1d(lam_nm, name="lam_nm")
    lam_m = lam_nm * NM_TO_M
    return fnu_w_m2_hz / (PLANCK_J_S * lam_m) * NM_TO_M


def ab_mag_to_photon_flux_per_nm(m_ab: float, lam_nm: np.ndarray) -> np.ndarray:
    """Convert AB magnitude directly to photon flux density per nm."""
    fnu_w_m2_hz = ab_mag_to_fnu_w_m2_hz(m_ab)
    return fnu_to_photon_flux_per_nm(fnu_w_m2_hz, lam_nm)
