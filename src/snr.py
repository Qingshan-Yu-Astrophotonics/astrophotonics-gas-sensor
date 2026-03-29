"""Count-rate and signal-to-noise calculations."""

from __future__ import annotations

import math

import numpy as np

from .source_flux import ab_mag_to_photon_flux_per_nm
from .utils import delta_lambda_nm, ensure_non_negative, ensure_positive


def source_counts(
    lam_nm: np.ndarray,
    eta_sys: np.ndarray,
    m_ab: float,
    area_m2: float,
    t_exp_s: float,
) -> float:
    """Compute source photo-electron counts over the wavelength band."""
    ensure_positive("area_m2", area_m2)
    ensure_positive("t_exp_s", t_exp_s)
    photon_flux = ab_mag_to_photon_flux_per_nm(m_ab, lam_nm)
    counts = t_exp_s * area_m2 * np.sum(photon_flux * eta_sys * delta_lambda_nm(lam_nm))
    return float(counts)


def sky_counts(
    lam_nm: np.ndarray,
    eta_sys: np.ndarray,
    sky_flux_per_nm_arcsec2: np.ndarray,
    area_m2: float,
    omega_ap_arcsec2: float,
    t_exp_s: float,
) -> float:
    """Compute sky-background photo-electron counts over the wavelength band."""
    ensure_positive("area_m2", area_m2)
    ensure_positive("t_exp_s", t_exp_s)
    ensure_non_negative("omega_ap_arcsec2", omega_ap_arcsec2)
    counts = (
        t_exp_s
        * area_m2
        * omega_ap_arcsec2
        * np.sum(sky_flux_per_nm_arcsec2 * eta_sys * delta_lambda_nm(lam_nm))
    )
    return float(counts)


def dark_counts(dark_current_e_s_pix: float, t_exp_s: float, n_pix: int) -> float:
    """Compute dark-current counts for one effective total exposure."""
    ensure_non_negative("dark_current_e_s_pix", dark_current_e_s_pix)
    ensure_positive("t_exp_s", t_exp_s)
    if n_pix <= 0:
        raise ValueError("n_pix must be positive.")
    return float(dark_current_e_s_pix * t_exp_s * n_pix)


def compute_snr(
    source_counts_e: float,
    sky_counts_e: float,
    dark_counts_e: float,
    read_noise_e_pix: float,
    n_pix: int,
    n_exp: int = 1,
) -> float:
    """Compute count-limited SNR including sky, dark, and read noise."""
    ensure_non_negative("source_counts_e", source_counts_e)
    ensure_non_negative("sky_counts_e", sky_counts_e)
    ensure_non_negative("dark_counts_e", dark_counts_e)
    ensure_non_negative("read_noise_e_pix", read_noise_e_pix)
    if n_pix <= 0 or n_exp <= 0:
        raise ValueError("n_pix and n_exp must be positive integers.")
    variance = source_counts_e + sky_counts_e + dark_counts_e + n_exp * n_pix * read_noise_e_pix**2
    if variance <= 0.0:
        return 0.0
    return float(source_counts_e / math.sqrt(variance))


def stacked_snr(
    lam_nm: np.ndarray,
    eta_sys: np.ndarray,
    m_ab: float,
    area_m2: float,
    sky_flux_per_nm_arcsec2: np.ndarray,
    omega_ap_arcsec2: float,
    dark_current_e_s_pix: float,
    read_noise_e_pix: float,
    n_pix: int,
    t_total_s: float,
    t_exp_s: float,
) -> dict[str, float]:
    """Compute SNR and component counts for a stacked observation."""
    ensure_positive("t_total_s", t_total_s)
    ensure_positive("t_exp_s", t_exp_s)
    n_exp = max(1, int(math.ceil(t_total_s / t_exp_s)))
    ns = source_counts(lam_nm, eta_sys, m_ab, area_m2, t_total_s)
    nsky = sky_counts(lam_nm, eta_sys, sky_flux_per_nm_arcsec2, area_m2, omega_ap_arcsec2, t_total_s)
    ndark = dark_counts(dark_current_e_s_pix, t_total_s, n_pix)
    snr_value = compute_snr(ns, nsky, ndark, read_noise_e_pix, n_pix, n_exp=n_exp)
    return {
        "snr": snr_value,
        "source_counts_e": ns,
        "sky_counts_e": nsky,
        "dark_counts_e": ndark,
        "n_exp": float(n_exp),
    }
