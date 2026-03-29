from __future__ import annotations

from copy import deepcopy
import unittest

import numpy as np

from src.config_loader import load_config_bundle
from src.lantern_surrogate import LanternInternalModel
from src.limiting_mag import solve_limiting_mag
from src.sky_background import sky_photon_flux_per_nm_arcsec2
from src.snr import stacked_snr
from src.system_model import SystemModel
from src.telescope import effective_collecting_area


CONFIG = load_config_bundle("config")
LAM_NM = CONFIG["lam_nm"]
BASE = CONFIG["base"]
TELESCOPE = CONFIG["telescope"]
DETECTOR = CONFIG["detector"]
SKY_FLUX = sky_photon_flux_per_nm_arcsec2(LAM_NM, BASE["sky"])


def build_model(n_port: int = 7, eta_inj: float | None = None) -> tuple[LanternInternalModel, SystemModel]:
    lantern_cfg = deepcopy(BASE["lantern"])
    lantern = LanternInternalModel(
        n_port=n_port,
        lambda0_nm=float(lantern_cfg["lambda0_nm"]),
        alpha_ad=float(lantern_cfg["alpha_ad"]),
        eta0=float(lantern_cfg["eta0"]),
        sigma_mix=float(lantern_cfg["sigma_mix"]),
        w_cut=float(lantern_cfg["w_cut"]),
        input_profile=str(lantern_cfg["input_profile"]),
        port_map_mode=str(lantern_cfg["port_map_mode"]),
        random_seed=int(lantern_cfg["random_seed"]),
    )
    telescope_cfg = deepcopy(TELESCOPE)
    if eta_inj is not None:
        telescope_cfg["eta_inj"] = eta_inj
    system = SystemModel(telescope_cfg=telescope_cfg, detector_cfg_raw=DETECTOR, lantern_model=lantern)
    return lantern, system


def snr_for_mag(system: SystemModel, m_ab: float, t_total_s: float) -> float:
    detector = system.detector
    return stacked_snr(
        lam_nm=LAM_NM,
        eta_sys=system.eta_sys(LAM_NM),
        m_ab=m_ab,
        area_m2=system.effective_area_m2(),
        sky_flux_per_nm_arcsec2=SKY_FLUX,
        omega_ap_arcsec2=float(system.telescope_cfg["omega_ap_arcsec2"]),
        dark_current_e_s_pix=detector.dark_current_e_s_pix,
        read_noise_e_pix=detector.read_noise_e_pix,
        n_pix=detector.n_pix,
        t_total_s=t_total_s,
        t_exp_s=float(BASE["observation"]["exposure_time_s"]),
    )["snr"]


class SanityChecks(unittest.TestCase):
    def test_eta_internal_bounded(self) -> None:
        lantern, _ = build_model()
        eta_internal = lantern.eta_internal(LAM_NM)
        self.assertTrue(np.all(eta_internal >= 0.0))
        self.assertTrue(np.all(eta_internal <= 1.0))

    def test_propagated_power_is_bounded_by_internal_throughput(self) -> None:
        lantern, _ = build_model()
        p_in = lantern.generate_input_modes(n_mode_in=21)
        payload = lantern.propagate_power(p_in=p_in, lam_nm=np.array([950.0]))
        self.assertLessEqual(payload["p_out"].sum(), payload["eta_internal"] + 1e-12)

    def test_effective_area_positive(self) -> None:
        self.assertGreater(effective_collecting_area(1.0, 0.2), 0.0)

    def test_brighter_source_has_higher_snr(self) -> None:
        _, system = build_model()
        self.assertGreater(snr_for_mag(system, m_ab=16.0, t_total_s=900.0), snr_for_mag(system, m_ab=19.0, t_total_s=900.0))

    def test_limiting_magnitude_non_decreasing_with_time(self) -> None:
        _, system = build_model()

        def factory(t_total_s: float):
            return lambda m_ab: snr_for_mag(system, m_ab=m_ab, t_total_s=t_total_s)

        times = [60.0, 300.0, 900.0, 3600.0]
        m_lim = [
            solve_limiting_mag(factory(t_total_s), snr_target=float(BASE["snr_target"]), bracket_mag=(-5.0, 35.0))
            for t_total_s in times
        ]
        self.assertTrue(np.all(np.diff(m_lim) >= -1e-8))

    def test_higher_throughput_yields_deeper_limiting_magnitude(self) -> None:
        _, system_lo = build_model(eta_inj=0.4)
        _, system_hi = build_model(eta_inj=0.7)
        t_total_s = 3600.0

        m_lim_lo = solve_limiting_mag(
            lambda m_ab: snr_for_mag(system_lo, m_ab=m_ab, t_total_s=t_total_s),
            snr_target=float(BASE["snr_target"]),
            bracket_mag=(-5.0, 35.0),
        )
        m_lim_hi = solve_limiting_mag(
            lambda m_ab: snr_for_mag(system_hi, m_ab=m_ab, t_total_s=t_total_s),
            snr_target=float(BASE["snr_target"]),
            bracket_mag=(-5.0, 35.0),
        )
        self.assertGreater(m_lim_hi, m_lim_lo)


if __name__ == "__main__":
    unittest.main()
