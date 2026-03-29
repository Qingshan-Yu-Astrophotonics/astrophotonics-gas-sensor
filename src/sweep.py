"""Scenario sweeps and result packaging for the surrogate model."""

from __future__ import annotations

from copy import deepcopy

import numpy as np
import pandas as pd

from .config_loader import deep_merge_dicts
from .lantern_surrogate import LanternInternalModel
from .limiting_mag import solve_limiting_mag, sweep_limiting_mag_vs_time
from .sky_background import sky_photon_flux_per_nm_arcsec2
from .snr import stacked_snr
from .system_model import SystemModel
from .utils import band_average


def build_mag_grid(source_cfg: dict) -> np.ndarray:
    """Construct the plotting magnitude grid from config."""
    grid_cfg = source_cfg["m_ab_grid"]
    return np.arange(grid_cfg["start_mag"], grid_cfg["stop_mag"] + 0.5 * grid_cfg["step_mag"], grid_cfg["step_mag"])


def run_sweep(config_bundle: dict) -> dict:
    """Run the requested lantern port sweep and package all outputs."""
    base_cfg = deepcopy(config_bundle["base"])
    telescope_cfg = deepcopy(config_bundle["telescope"])
    detector_cfg = deepcopy(config_bundle["detector"])
    lam_nm = config_bundle["lam_nm"]
    sky_flux = sky_photon_flux_per_nm_arcsec2(lam_nm, base_cfg["sky"])
    mag_grid = build_mag_grid(base_cfg["source"])
    t_total_values = [float(value) for value in base_cfg["observation"]["t_total_s"]]
    target_total_time_s = float(base_cfg["observation"]["target_total_time_s"])
    exposure_time_s = float(base_cfg["observation"]["exposure_time_s"])
    snr_target = float(base_cfg["snr_target"])
    bracket_mag = tuple(float(value) for value in base_cfg["source"]["root_bracket_mag"])
    port_lambda_nm = float(base_cfg["lantern"]["port_distribution_lambda_nm"])

    scenario_results: list[dict] = []
    eta_internal_rows: list[dict] = []
    eta_sys_rows: list[dict] = []
    limiting_rows: list[dict] = []

    for scenario_cfg in config_bundle["scenarios"]:
        lantern_cfg = deep_merge_dicts(base_cfg["lantern"], scenario_cfg.get("lantern", {}))
        lantern_model = LanternInternalModel(
            n_port=int(scenario_cfg["n_port"]),
            lambda0_nm=float(lantern_cfg["lambda0_nm"]),
            alpha_ad=float(lantern_cfg["alpha_ad"]),
            eta0=float(lantern_cfg["eta0"]),
            sigma_mix=float(lantern_cfg["sigma_mix"]),
            w_cut=float(lantern_cfg["w_cut"]),
            input_profile=str(lantern_cfg.get("input_profile", "uniform")),
            port_map_mode=str(lantern_cfg.get("port_map_mode", "uniform")),
            random_seed=int(lantern_cfg.get("random_seed", 12345)),
        )
        system_model = SystemModel(telescope_cfg=telescope_cfg, detector_cfg_raw=detector_cfg, lantern_model=lantern_model)
        components = system_model.component_curves(lam_nm)
        eta_sys = components["eta_sys"]
        eta_internal = components["eta_internal"]
        area_m2 = system_model.effective_area_m2()
        omega_ap_arcsec2 = float(telescope_cfg["omega_ap_arcsec2"])
        detector = system_model.detector

        def snr_fn_factory(t_total_s: float):
            def snr_at_mag(m_ab: float) -> float:
                return stacked_snr(
                    lam_nm=lam_nm,
                    eta_sys=eta_sys,
                    m_ab=m_ab,
                    area_m2=area_m2,
                    sky_flux_per_nm_arcsec2=sky_flux,
                    omega_ap_arcsec2=omega_ap_arcsec2,
                    dark_current_e_s_pix=detector.dark_current_e_s_pix,
                    read_noise_e_pix=detector.read_noise_e_pix,
                    n_pix=detector.n_pix,
                    t_total_s=t_total_s,
                    t_exp_s=exposure_time_s,
                )["snr"]

            return snr_at_mag

        snr_grid = np.array([snr_fn_factory(target_total_time_s)(m_ab) for m_ab in mag_grid], dtype=float)
        m_lim_target = solve_limiting_mag(snr_fn_factory(target_total_time_s), snr_target=snr_target, bracket_mag=bracket_mag)
        m_lim_vs_time = sweep_limiting_mag_vs_time(
            t_total_s_values=t_total_values,
            snr_fn_factory=snr_fn_factory,
            snr_target=snr_target,
            bracket_mag=bracket_mag,
        )

        n_mode_in = max(lantern_model.n_port * 3, int(np.ceil(lantern_model.mm_mode_count(np.array([lam_nm.min()]))[0])))
        port_payload = lantern_model.propagate_power(
            p_in=lantern_model.generate_input_modes(n_mode_in=n_mode_in),
            lam_nm=np.array([port_lambda_nm]),
        )

        for idx, lam_value in enumerate(lam_nm):
            eta_internal_rows.append(
                {
                    "scenario": scenario_cfg["name"],
                    "n_port": lantern_model.n_port,
                    "lam_nm": float(lam_value),
                    "mm_mode_count": float(lantern_model.mm_mode_count(np.array([lam_value]))[0]),
                    "eta_match": float(lantern_model.eta_match(np.array([lam_value]))[0]),
                    "eta_ad": float(lantern_model.eta_ad(np.array([lam_value]))[0]),
                    "eta_internal": float(eta_internal[idx]),
                }
            )
            eta_sys_rows.append(
                {
                    "scenario": scenario_cfg["name"],
                    "n_port": lantern_model.n_port,
                    "lam_nm": float(lam_value),
                    "eta_atm": float(components["eta_atm"][idx]),
                    "eta_tel": float(components["eta_tel"][idx]),
                    "eta_fore": float(components["eta_fore"][idx]),
                    "eta_inj": float(components["eta_inj"][idx]),
                    "eta_internal": float(components["eta_internal"][idx]),
                    "qe": float(components["qe"][idx]),
                    "eta_sys": float(components["eta_sys"][idx]),
                }
            )

        for row in m_lim_vs_time:
            limiting_rows.append(
                {
                    "scenario": scenario_cfg["name"],
                    "n_port": lantern_model.n_port,
                    "t_total_s": row["t_total_s"],
                    "snr_target": snr_target,
                    "m_lim": row["m_lim"],
                    "eta_internal_bandavg": band_average(eta_internal),
                    "eta_sys_bandavg": band_average(eta_sys),
                }
            )

        scenario_results.append(
            {
                "name": scenario_cfg["name"],
                "n_port": lantern_model.n_port,
                "lam_nm": lam_nm,
                "mode_count": lantern_model.mm_mode_count(lam_nm),
                "eta_match": lantern_model.eta_match(lam_nm),
                "eta_internal": eta_internal,
                "eta_sys": eta_sys,
                "snr_grid": snr_grid,
                "m_ab_grid": mag_grid,
                "m_lim_target": m_lim_target,
                "m_lim_vs_time": m_lim_vs_time,
                "eta_internal_bandavg": band_average(eta_internal),
                "eta_sys_bandavg": band_average(eta_sys),
                "port_payload": port_payload,
            }
        )

    return {
        "lam_nm": lam_nm,
        "m_ab_grid": mag_grid,
        "t_total_s": t_total_values,
        "scenario_results": scenario_results,
        "eta_internal_summary": pd.DataFrame(eta_internal_rows),
        "eta_sys_summary": pd.DataFrame(eta_sys_rows),
        "limiting_magnitude_summary": pd.DataFrame(limiting_rows),
    }
