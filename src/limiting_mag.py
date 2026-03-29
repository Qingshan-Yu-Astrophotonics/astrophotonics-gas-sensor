"""Limiting magnitude solvers for the surrogate observation model."""

from __future__ import annotations

from collections.abc import Callable, Iterable

from scipy.optimize import brentq


def solve_limiting_mag(
    snr_fn: Callable[[float], float],
    snr_target: float,
    bracket_mag: tuple[float, float] = (-5.0, 35.0),
) -> float:
    """Solve for the AB magnitude that reaches the target SNR."""
    lo_mag, hi_mag = bracket_mag
    f_lo = snr_fn(lo_mag) - snr_target
    f_hi = snr_fn(hi_mag) - snr_target
    if f_lo == 0.0:
        return float(lo_mag)
    if f_hi == 0.0:
        return float(hi_mag)
    if f_lo * f_hi > 0.0:
        raise ValueError(
            "Limiting magnitude root not bracketed. "
            f"SNR({lo_mag})={f_lo + snr_target:.4f}, SNR({hi_mag})={f_hi + snr_target:.4f}."
        )
    return float(brentq(lambda mag: snr_fn(mag) - snr_target, lo_mag, hi_mag))


def sweep_limiting_mag_vs_time(
    t_total_s_values: Iterable[float],
    snr_fn_factory: Callable[[float], Callable[[float], float]],
    snr_target: float,
    bracket_mag: tuple[float, float] = (-5.0, 35.0),
) -> list[dict[str, float]]:
    """Solve limiting magnitude over a list of total integration times."""
    results: list[dict[str, float]] = []
    for t_total_s in t_total_s_values:
        snr_fn = snr_fn_factory(float(t_total_s))
        m_lim = solve_limiting_mag(snr_fn=snr_fn, snr_target=snr_target, bracket_mag=bracket_mag)
        results.append({"t_total_s": float(t_total_s), "m_lim": m_lim})
    return results
